import os
from openai import OpenAI
from llm_tracekit import OpenAIInstrumentor, setup_export_to_coralogix

# Configure export to Coralogix
setup_export_to_coralogix(
    service_name="ai-demo-service",
    application_name="ai-demo-app",
    subsystem_name="getting-started"
)

# Instrument OpenAI client
OpenAIInstrumentor().instrument()

# Initialize OpenAI client
client = OpenAI()

# Send a request to OpenAI
def generate_content():
    print("Sending request to OpenAI...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Explain what AI observability is in one sentence."},
        ],
    )

    # Display a nicer formatted response
    print("\n" + "="*50)
    print("📝 AI RESPONSE:")
    print(f"{response.choices[0].message.content}")
    print("="*50)

    # Confirmation about traces
    print("\n✅ Traces have been successfully sent to Coralogix AI Center!")
    print("View your data in the Coralogix AI Center dashboard.\n")

if __name__ == "__main__":
    generate_content()