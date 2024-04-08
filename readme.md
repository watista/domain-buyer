# Openprovider Domain Buyer Script
Script to automatically buy domains via Openprovider.

## Getting started
### Installing packages and venv setup
Install the required packages
```
apt install build-essential libssl-dev libffi-dev
apt install python3-dev python3-venv python3-pip python3-setuptools
```

Clone the repository, create the python environment and install required pip packages
```
git clone
cd ./domain-buyer
python3 -m venv pythonenv
source pythonenv/bin/activate
pip install -r requirements.txt
deactivate
```

### Environment variables and tokens
Create in the root folder a file called `.env` with the below contents, or set them as environment variables
```
BOT_TOKEN=123123
USERNAME=test123
PASSWORD=test123
LOG_TYPE=INFO
```
*LOG_TYPE* can be one of: `ERROR`, `WARNING`, `INFO`, `DEBUG`

## Usage
```
# Run the script
./domain-buyer/pythonenv/bin/python3 ./domain-buyer/main.py
# or
source ./domain-buyer/pythonenv/bin/activate
python3 ./domain-buyer/main.py

# Arguments
./main.py -h         # Show help
./main.py -v         # Show console output
./main.py --verbose  # Show console output

```
