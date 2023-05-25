import streamlit as st
from dotenv import load_dotenv
import boto3
import logging
from datetime import datetime
import time
import os

load_dotenv()

# Configure logging
logging.basicConfig(filename='ec2_health.log', level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Function to check the health status of EC2 machines
def check_health(ec2_instance_ids):
    ec2 = boto3.client('ec2', aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'), aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))
    health_status = []
    for instance_id in ec2_instance_ids:
        response = ec2.describe_instance_status(InstanceIds=[instance_id])
        if len(response['InstanceStatuses']) > 0:
            instance_status = response['InstanceStatuses'][0]['InstanceStatus']['Status']
            health_status.append(instance_status)
            logging.info(f'[ECS] Health Status: Instance ID: {instance_id}, Status: {instance_status}')
    return health_status

# Function to start an EC2 machine
def start_instance(instance_id):
    ec2 = boto3.client('ec2', aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'), aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))
    response = ec2.start_instances(InstanceIds=[instance_id])
    logging.info(f'[ECS] Start: Instance ID: {instance_id}, Response: {response}')
    return response

# Function to stop an EC2 machine
def stop_instance(instance_id):
    ec2 = boto3.client('ec2', aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'), aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))
    response = ec2.stop_instances(InstanceIds=[instance_id])
    logging.info(f'[ECS] Stop: Instance ID: {instance_id}, Response: {response}')
    return response

# Function to check if the instance has reached the desired state
def check_instance_state(instance_id, desired_state):
    ec2 = boto3.client('ec2', aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'), aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))
    while True:
        response = ec2.describe_instances(InstanceIds=[instance_id])
        if len(response['Reservations']) > 0:
            instance_state = response['Reservations'][0]['Instances'][0]['State']['Name']
            if instance_state == desired_state:
                break
        time.sleep(5)

# Streamlit app
def main():
    st.title('EC2 Health Status')

    st.subheader('AWS Credentials')

    # Check if environment variables for access keys are set
    if 'AWS_ACCESS_KEY_ID' in os.environ and 'AWS_SECRET_ACCESS_KEY' in os.environ:
        access_key = os.environ['AWS_ACCESS_KEY_ID']
        secret_key = os.environ['AWS_SECRET_ACCESS_KEY']
    else:
        access_key = st.text_input('Access Key')
        secret_key = st.text_input('Secret Key', type='password')

    # EC2 instance IDs input
    instance_ids_input = st.text_input('EC2 Instance IDs (comma-separated)', help='Enter the EC2 instance IDs separated by commas')
    ec2_instance_ids = [instance.strip() for instance in instance_ids_input.split(',')] if instance_ids_input else []

    # Check the health status of EC2 machines
    health_status = check_health(ec2_instance_ids)

    # Update the color of the status bar based on the instance status
    for i, status in enumerate(health_status):
        if status == 'ok':
            st.success(f'Instance {i+1}: {status}')
        else:
            st.error(f'Instance {i+1}: {status}')

    # Columns to start and stop EC2 machines
    col1, col2 = st.columns(2)
    with col1:
        if st.button('Start EC2 Machines'):
            for instance_id in ec2_instance_ids:
                st.write(f'Starting instance {instance_id}')
                start_instance(instance_id)
                with st.spinner('Waiting for instance to start...'):
                    check_instance_state(instance_id, 'running')
                st.success(f'Instance {instance_id} started successfully!')
    with col2:
        if st.button('Stop EC2 Machines'):
            for instance_id in ec2_instance_ids:
                st.write(f'Stopping instance {instance_id}')
                stop_instance(instance_id)
                with st.spinner('Waiting for instance to stop...'):
                    check_instance_state(instance_id, 'stopped')
                st.error(f'Instance {instance_id} stopped successfully!')

if __name__ == '__main__':
    main()
