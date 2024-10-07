import requests


def test_health_check() -> None:
    """
    Test the health check endpoint of the booking service. The health check endpoint should
    return a 200 status code and a JSON response
    """
    response = requests.get("https://dev.dashwu.xyz/ping/")
    assert response.status_code == 200
    assert response.json() == {"message": "ok"}
