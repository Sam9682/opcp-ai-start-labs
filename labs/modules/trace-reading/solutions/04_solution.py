"""Reference solution for Exercise 4: Spot the Guardrail Trigger."""


def submission() -> dict:
    return {
        "guardrail_layer": "operational_limits",
        "prevented_action": "another deploy_app retry attempt",
    }
