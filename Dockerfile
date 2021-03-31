FROM python:3.7

WORKDIR /rockx-market
COPY .  /rockx-market

#setup python dependencies
RUN pip install -r requirements.txt

EXPOSE  5000
CMD ["python", "src/main.py"]
