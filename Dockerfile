# Pinned to the interpreter line the deployed images were built with.
# mjml-python is resolved from requirements.txt (pinned versions) at build time.
FROM python:3.14

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT [ "python", "/usr/src/app/app/report.py", "--sr-data", "/sr-data" ]
