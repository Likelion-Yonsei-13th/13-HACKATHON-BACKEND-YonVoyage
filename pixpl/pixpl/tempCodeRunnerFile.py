import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from decouple import config

def check_aws_keys():
    aws_access_key_id = config("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = config("AWS_SECRET_ACCESS_KEY")
    aws_region = config("AWS_S3_REGION_NAME")
    bucket_name = config("AWS_STORAGE_BUCKET_NAME")

    try:
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region
        )
        s3 = session.client('s3')

        # 버킷 접근 테스트
        response = s3.list_objects_v2(Bucket=bucket_name)
        print("✅ AWS 키 유효, 버킷 접근 성공")
        for obj in response.get('Contents', []):
            print("-", obj['Key'])

    except NoCredentialsError:
        print("❌ AWS 키가 설정되지 않았거나 잘못됨")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code in ['InvalidAccessKeyId', 'SignatureDoesNotMatch']:
            print("❌ AWS 키가 잘못됨")
        elif error_code == 'AccessDenied':
            print("❌ IAM 권한 문제: 키는 유효하지만 접근 권한이 없음")
        else:
            print("❌ 기타 오류:", e)

# 실행
check_aws_keys()
