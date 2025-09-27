from transformers import AutoTokenizer, AutoModelForCausalLM

# Use the DialoGPT-small model
model_id = "microsoft/DialoGPT-small"

# Download the model and tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id)

# Save them locally
model.save_pretrained("chatbot_model")
tokenizer.save_pretrained("chatbot_model")

print("Model downloaded and saved to chatbot_model/")
