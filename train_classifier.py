import os
# Force transformers to use PyTorch and avoid heavy TensorFlow imports
os.environ["USE_TORCH"] = "1"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
import torch

def prepare_and_train(csv_path, output_dir, num_labels=4):
    if not os.path.exists(csv_path):
        print(f"File {csv_path} not found. Create it with 'text,label' format.")
        return

    # Load & preprocess
    dataset = load_dataset("csv", data_files=csv_path)
    # Split for evaluation
    dataset = dataset["train"].train_test_split(test_size=0.2)

    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")

    def tokenize(batch):
        return tokenizer(batch["text"], truncation=True, padding=True)

    dataset = dataset.map(tokenize, batched=True)
    dataset = dataset.rename_column("label", "labels")
    dataset.set_format("torch", columns=["input_ids", "attention_mask", "labels"])

    # Train
    model = AutoModelForSequenceClassification.from_pretrained(
        "distilbert-base-uncased",
        num_labels=num_labels
    )

    training_args = TrainingArguments(
        output_dir=output_dir,
        evaluation_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=16,
        num_train_epochs=3,
        weight_decay=0.01,
        logging_dir=f"./logs/{os.path.basename(output_dir)}",
        use_mps_device=torch.backends.mps.is_available()
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["test"]
    )

    print(f"Starting training for {output_dir}...")
    trainer.train()
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"Model saved to {output_dir}")

if __name__ == "__main__":
    # Example usage (commented out to prevent accidental execution if data is missing)
    # prepare_and_train("emails_purpose.csv", "./email_classifier_purpose", num_labels=4)
    # prepare_and_train("emails_topic.csv", "./email_classifier_topic", num_labels=10)
    pass
