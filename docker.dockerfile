FROM python:3.8.3

COPY src input data_structural fhi_xx_02/

ENTRYPOINT ["python", "src/main.py"]