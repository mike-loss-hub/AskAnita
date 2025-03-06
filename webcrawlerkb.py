import boto3
import time
import json
from datetime import datetime
from app import load_dotStreat_sl

def create_bedrock_role():
    iam = boto3.client('iam')
    
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    try:
        role = iam.create_role(
            RoleName='BedrockKnowledgeBaseRole',
            AssumeRolePolicyDocument=json.dumps(trust_policy)
        )
        
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:*",
                        "aoss:*"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        iam.put_role_policy(
            RoleName='BedrockKnowledgeBaseRole',
            PolicyName='BedrockKnowledgeBasePolicy',
            PolicyDocument=json.dumps(policy)
        )
        
        return role['Role']['Arn']
    except iam.exceptions.EntityAlreadyExistsException:
        role = iam.get_role(RoleName='BedrockKnowledgeBaseRole')
        return role['Role']['Arn']



def create_web_crawler_knowledge_base(website_url, kb_name):
    bedrock = boto3.client('bedrock-agent')
    
    # Create IAM role ARN - you need to replace this with your actual role ARN
    role_arn = "arn:aws:iam::957002132578:role/BedrockKnowledgeBaseRole"
    
    response = bedrock.create_knowledge_base(
        name=kb_name,
        description=f"Web crawler knowledge base for {website_url}",
        roleArn=role_arn,
        knowledgeBaseConfiguration={
            'type': 'VECTOR',
            'vectorKnowledgeBaseConfiguration': {
                'embeddingModelArn': 'arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v1',
                'embeddingModelConfiguration': {
                    'bedrockEmbeddingModelConfiguration': {
                        'dimensions': 1536,
                        'embeddingDataType': 'FLOAT32'
                    }
                }
            }
        }
    )
    
    knowledge_base_id = response['knowledgeBase']['knowledgeBaseId']
    
    # Configure web crawler data source
    data_source_response = bedrock.create_data_source(
        knowledgeBaseId=knowledge_base_id,
        name=f"{kb_name}-webcrawler",
        description=f"Web crawler for {website_url}",
        dataSourceConfiguration={
            'type': 'WEB_CRAWLER',
            'webCrawlerConfiguration': {
                'urls': [{
                    'uri': 'https://www.ena.org',
                    'crawlMode': 'FULL_SITE',
                    'crawlDepth': 10
                }],
                'webCrawlerParameters': {
                    'maxUrlsPerMinute': 60,
                    'maxLinksPerPage': 100,
                    'maxFileSize': 10485760,
                    'inclusionPatterns': [
                        'https://www.ena.org/*'
                    ],
                    'exclusionPatterns': [
                        '*/login*',
                        '*/cart*',
                        '*/search*',
                        '*.jpg',
                        '*.png',
                        '*.gif'
                    ],
                    'respectRobotsTxt': True
                }
            }
        }
    )
    
    return {
        'knowledge_base_id': knowledge_base_id,
        'data_source_id': data_source_response['dataSource']['dataSourceId']
    }

def main():
    website_url = 'https://www.ena.org'
    kb_name = f"ENA-Website-KB-{datetime.now().strftime('%Y%m%d')}"
    load_dotStreat_sl()
    try:
        print(f"Creating knowledge base for {website_url}...")
        result = create_web_crawler_knowledge_base(website_url, kb_name)
        
        print("Knowledge base created successfully")
        print(f"Knowledge Base ID: {result['knowledge_base_id']}")
        print(f"Data Source ID: {result['data_source_id']}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
