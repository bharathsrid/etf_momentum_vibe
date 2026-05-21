.PHONY: build deploy invoke logs delete validate

REGION := us-east-1
STACK  := etf-signals-daily

validate:
	sam validate --region $(REGION)

build:
	sam build

deploy: build
	sam deploy \
	  --stack-name $(STACK) \
	  --region $(REGION) \
	  --capabilities CAPABILITY_IAM \
	  --resolve-s3 \
	  --resolve-image-repos \
	  --no-confirm-changeset \
	  --no-fail-on-empty-changeset

# One-shot invoke against the deployed function.
invoke:
	aws lambda invoke \
	  --function-name etf-signals-daily \
	  --region $(REGION) \
	  --profile nshq \
	  --cli-binary-format raw-in-base64-out \
	  --payload '{}' \
	  /tmp/etf-signals-out.json && cat /tmp/etf-signals-out.json

logs:
	sam logs --stack-name $(STACK) --region $(REGION) --tail

delete:
	sam delete --stack-name $(STACK) --region $(REGION) --no-prompts
