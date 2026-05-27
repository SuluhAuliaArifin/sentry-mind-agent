from synapse_sap_sdk import Agent

def register(wallet):
    agent = Agent(
        name="sentry-mind-agent",
        wallet=wallet
    )
    return agent.register()