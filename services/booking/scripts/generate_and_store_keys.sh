#!/bin/bash

# Function to prompt user for AWS credentials profile and environment
prompt_for_input() {
  echo "Please enter the AWS credentials profile to use:"
  read -r AWS_PROFILE

  echo "Please enter the environment (prod or dev):"
  read -r ENV
}

# Function to generate Ed25519 private and public keys
generate_keys() {
  echo "Generating Ed25519 key pair..."

  # Generate private key and store it in a temp file
  PRIVATE_KEY_FILE=$(mktemp)
  PUBLIC_KEY_FILE=$(mktemp)

  # Generate Ed25519 private key
  openssl genpkey -algorithm Ed25519 -out "$PRIVATE_KEY_FILE"

  if [ $? -ne 0 ]; then
    echo "Error generating private key. Please ensure openssl is installed correctly."
    exit 1
  fi

  # Extract the public key from the private key
  openssl pkey -in "$PRIVATE_KEY_FILE" -pubout -out "$PUBLIC_KEY_FILE"

  if [ $? -ne 0 ]; then
    echo "Error generating public key from private key."
    exit 1
  fi

  # Base64 encode the private and public keys
  PRIVATE_KEY=$(base64 < "$PRIVATE_KEY_FILE")
  PUBLIC_KEY=$(base64 < "$PUBLIC_KEY_FILE")

  # Cleanup temp files
  rm "$PRIVATE_KEY_FILE" "$PUBLIC_KEY_FILE"

  if [[ -z "$PRIVATE_KEY" || -z "$PUBLIC_KEY" ]]; then
    echo "Error: Empty keys generated."
    exit 1
  fi

  echo "Keys generated successfully."
}

# Function to store the keys in AWS Secrets Manager
store_keys_in_secrets_manager() {
  echo "Storing private key in AWS Secrets Manager..."
  
  # Suppressing AWS CLI output by redirecting stdout and stderr to /dev/null
  aws secretsmanager put-secret-value \
    --secret-id "private_key_${ENV}" \
    --secret-string "$PRIVATE_KEY" \
    --profile "$AWS_PROFILE" > /dev/null 2>&1

  if [ $? -ne 0 ]; then
    echo "Failed to store private key"
    exit 1
  fi

  echo "Private key stored successfully."

  echo "Storing public key in AWS Secrets Manager..."

  # Suppressing AWS CLI output by redirecting stdout and stderr to /dev/null
  aws secretsmanager put-secret-value \
    --secret-id "public_key_${ENV}" \
    --secret-string "$PUBLIC_KEY" \
    --profile "$AWS_PROFILE" > /dev/null 2>&1

  if [ $? -ne 0 ]; then
    echo "Failed to store public key"
    exit 1
  fi

  echo "Public key stored successfully"
}

# Main script execution
prompt_for_input
generate_keys
store_keys_in_secrets_manager
