import logging
import sys
import time
from argparse import ArgumentParser
from typing import Collection, Dict, Sequence

import boto3
from mypy_boto3_ecs import ECSClient

logger = logging.getLogger(name="deploy_ecs")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
TaskDefinition = Dict[str, Collection[Collection[str]]]


def generate_task_definition(env: str, image_uri: str) -> TaskDefinition:
    """
    Generate a new ECS task definition for the booking service.

    Parameters
    ----------
    env : str
        The deployment environment, either 'dev' or 'prod'.
    image_uri : str
        The URL of the Docker image to deploy.

    Returns
    -------
    task_definition : Dict
        The ECS task definition.
    """

    task_definition = {
        "containerDefinitions": [
            {
                "name": f"booking_service_{env}_ecs_fargate_container",
                "image": image_uri,
                "portMappings": [{"containerPort": 5000, "hostPort": 5000, "protocol": "tcp"}],
                "essential": True,
                "command": [
                    "gunicorn",
                    "--bind",
                    "0.0.0.0:5000",
                    "app.main:app",
                    "-k",
                    "uvicorn.workers.UvicornWorker",
                ],
                "environment": [
                    {"name": "ENV", "value": env},
                    {"name": "DOCS_URL", "value": "/docs" if env == "dev" else ""},
                ],
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-create-group": "true",  # See https://stackoverflow.com/questions/64209899/resourceinitializationerror-failed-to-validate-logger-args-signal-killed
                        "awslogs-group": f"/ecs/booking_service_{env}",
                        "awslogs-region": "us-east-1",
                        "awslogs-stream-prefix": f"booking_service_{env}_log_stream",
                    },
                },
            }
        ],
        "family": f"booking_service_{env}_ecs_fargate_task_definition",
        "taskRoleArn": f"arn:aws:iam::722696965592:role/booking_service_{env}_iam_ecs_task_role",
        "executionRoleArn": f"arn:aws:iam::722696965592:role/booking_service_{env}_iam_ecs_execution_role",
        "networkMode": "awsvpc",
        "volumes": [],
        "requiresCompatibilities": ["FARGATE"],
        "cpu": "512",
        "memory": "1024",
        "runtimePlatform": {"cpuArchitecture": "X86_64", "operatingSystemFamily": "LINUX"},
        "tags": [{"key": "Name", "value": f"booking_service_{env}_ecs_fargate_task_definition"}],
    }

    return task_definition


def migrations(
    env: str,
    ecs_client: ECSClient,
    cluster_name: str,
    task_definition_arn: str,
    subnet_ids: Sequence[str],
    security_group_id: Sequence[str],
) -> None:
    """
    Apply migrations to the database in a standalone container independent of the service. The same image for deployment is reused for the migration.

    Parameters
    ----------
    env : str
        The deployment environment, either 'dev' or 'prod'.
    ecs_client : ECSClient
        The ECS client.
    cluster_name : str
        The ECS cluster name.
    task_definition_arn : str
        The ARN of the ECS task definition.
    subnet_ids : Sequence[str]
        The subnet IDs for the ECS task.
    security_group_id : Sequence[str]
        The security group IDs for the ECS task.
    """
    response = ecs_client.run_task(
        cluster=cluster_name,
        taskDefinition=task_definition_arn,
        launchType="FARGATE",
        networkConfiguration={
            "awsvpcConfiguration": {
                "subnets": subnet_ids,
                "securityGroups": security_group_id,
                "assignPublicIp": "DISABLED",
            }
        },
        overrides={
            "containerOverrides": [
                {
                    "name": f"booking_service_{env}_ecs_fargate_container",
                    "command": "alembic -c migrations/alembic.ini upgrade head".split(),
                    "environment": [
                        {"name": "ENV", "value": env},
                    ],
                },
            ]
        },
    )
    logger.info(f"Running migrations in a standalone container: {response['tasks'][0]['taskArn']}")


def wait_for_service_stable(
    ecs_client: ECSClient,
    cluster_name: str,
    service_name: str,
    timeout: int = 1800,
    delay: int = 10,
):
    """
    Wait for ECS service to become stable and log task counts.

    Parameters
    ----------
    ecs_client : ECSClient
        The ECS client.
    cluster_name : str
        The ECS cluster name.
    service_name : str
        The ECS service name.
    timeout : int
        The maximum time to wait, in seconds.
    delay : int
        The time interval between status checks, in seconds.
    """
    waiter = ecs_client.get_waiter("services_stable")
    logger.info(f"Waiting for service {service_name} to stabilize...")

    start_time = time.time()

    while time.time() - start_time < timeout:
        # Describe the service to get task counts
        response = ecs_client.describe_services(cluster=cluster_name, services=[service_name])
        service = response["services"][0]
        running_count = service["runningCount"]
        pending_count = service["pendingCount"]
        desired_count = service["desiredCount"]

        logger.info(
            f"Service {service_name}: runningCount = {running_count}, pendingCount = {pending_count}, desiredCount = {desired_count}"
        )

        # Check if the desired count has been reached
        if running_count == desired_count:
            logger.info(
                f"Service {service_name} has reached the desired count of {desired_count} tasks"
            )
            break

        # Wait for the specified delay before checking again
        time.sleep(delay)

    if time.time() - start_time >= timeout:
        logger.error(f"Service {service_name} did not stabilize within {timeout} seconds")
        raise TimeoutError("Service stabilization timed out")

    # Use waiter to ensure the service is stable
    waiter.wait(
        cluster=cluster_name,
        services=[service_name],
        WaiterConfig={"Delay": delay, "MaxAttempts": timeout // delay},
    )
    logger.info(f"Service {service_name} is stable")


def main() -> int:

    timeout = 1800
    delay = 30

    parser = ArgumentParser(
        description="Register a new task definition, update the service, wait for the desired container count to satisfied"
    )
    parser.add_argument(
        "--env", type=str, required=True, help="The deployment environment, either 'dev' or 'prod'"
    )
    parser.add_argument(
        "--image_uri", type=str, required=True, help="The URL of the Docker image to deploy"
    )
    parser.add_argument(
        "--cluster_name", type=str, required=True, help="The name of the ECS cluster"
    )
    parser.add_argument(
        "--service_name", type=str, required=True, help="The name of the ECS service"
    )
    parser.add_argument(
        "--subnet_ids", type=str, nargs="+", required=True, help="The subnet IDs for the ECS task"
    )
    parser.add_argument(
        "--security_group_id",
        type=str,
        nargs="+",
        required=True,
        help="The security group ID for the ECS task",
    )
    args, _ = parser.parse_known_args()

    ecs_client: ECSClient = boto3.client("ecs")

    task_definition = generate_task_definition(env=args.env, image_uri=args.image_uri)
    response = ecs_client.register_task_definition(**task_definition)  # type: ignore
    task_definition_arn = response["taskDefinition"]["taskDefinitionArn"]
    logger.info(f"Registered new task definition: {task_definition_arn}")

    migrations(
        env=args.env,
        ecs_client=ecs_client,
        cluster_name=args.cluster_name,
        task_definition_arn=task_definition_arn,
        subnet_ids=args.subnet_ids,
        security_group_id=args.security_group_id,
    )

    response = ecs_client.update_service(
        cluster=args.cluster_name, service=args.service_name, taskDefinition=task_definition_arn
    )  # type: ignore
    logger.info(f"Updated service: {args.service_name}")

    # Wait for the service to stabilize
    wait_for_service_stable(
        ecs_client=ecs_client,
        cluster_name=args.cluster_name,
        service_name=args.service_name,
        timeout=timeout,
        delay=delay,
    )

    return 0


if __name__ == "__main__":

    main()
