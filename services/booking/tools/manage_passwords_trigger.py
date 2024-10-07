import logging
import sys
from argparse import ArgumentParser
from typing import Sequence

import boto3
from mypy_boto3_ecs import ECSClient

logger = logging.getLogger(name="manage_passwords")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)


def get_latest_task_definition(env: str, ecs_client: ECSClient) -> str:
    """
    Retrieve the latest task definition ARN for a given task family.

    Parameters
    ----------
    env : str
        The deployment environment, either 'dev' or 'prod'.
    ecs_client : ECSClient
        The ECS client instance.

    Returns
    -------
    str
        The latest task definition ARN.
    """
    family = f"booking_service_{env}_ecs_fargate_task_definition"
    try:
        response = ecs_client.describe_task_definition(
            taskDefinition=family,
        )
        return response["taskDefinition"]["taskDefinitionArn"]
    except Exception as error:
        logger.error(f"Failed to get latest task definition: {error}")
        raise


def manage_passwords_in_ecs(
    env: str,
    ecs_client: ECSClient,
    cluster_name: str,
    task_definition_arn: str,
    subnet_ids: Sequence[str],
    security_group_id: Sequence[str],
    username: str,
    role: str,
    disabled: bool,
) -> None:
    """
    Run the password rotation script in a standalone ECS Fargate task.

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
    username : str
        The username for which the password is being rotated.
    role : str
        The role of the user (e.g., 'admin' or 'requester').
    disabled : bool
        Whether the user account is disabled.
    """
    # Create the command to run the password rotation script
    command = [
        "python3",
        "tools/manage_passwords.py",
        "--env",
        env,
        "--username",
        username,
        "--role",
        role,
    ]

    if disabled:
        command.append("--disabled")

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
                    "command": command,
                    "environment": [
                        {"name": "ENV", "value": env},
                    ],
                },
            ]
        },
    )

    task_arn = response["tasks"][0]["taskArn"]
    logger.info(f"Running password rotation script in ECS Fargate container: {task_arn}")


def main() -> int:

    parser = ArgumentParser(description="Run password rotation in ECS Fargate task.")
    parser.add_argument(
        "--env", type=str, required=True, help="The deployment environment (e.g., 'dev' or 'prod')"
    )
    parser.add_argument(
        "--username", type=str, required=True, help="The username whose password is being rotated"
    )
    parser.add_argument(
        "--role", type=str, required=True, help="The role of the user (e.g., 'admin', 'requester')"
    )
    parser.add_argument(
        "--disabled", action="store_true", help="Whether the user account is disabled"
    )
    parser.add_argument(
        "--cluster_name", type=str, required=True, help="The name of the ECS cluster"
    )
    parser.add_argument(
        "--subnet_ids", type=str, nargs="+", required=True, help="The subnet IDs for the ECS task"
    )
    parser.add_argument(
        "--security_group_id",
        type=str,
        nargs="+",
        required=True,
        help="The security group IDs for the ECS task",
    )
    args, _ = parser.parse_known_args()

    ecs_client: ECSClient = boto3.client("ecs")

    task_definition_arn = get_latest_task_definition(args.env, ecs_client)

    manage_passwords_in_ecs(
        env=args.env,
        ecs_client=ecs_client,
        cluster_name=args.cluster_name,
        task_definition_arn=task_definition_arn,
        subnet_ids=args.subnet_ids,
        security_group_id=args.security_group_id,
        username=args.username,
        role=args.role,
        disabled=args.disabled,
    )

    return 0


if __name__ == "__main__":

    main()
