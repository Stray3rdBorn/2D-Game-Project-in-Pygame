FROM python:3.13-slim

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Collect the admin page CSS so the server can serve it
RUN SECRET_KEY=build DATABASE_URL=sqlite:// python web/manage.py collectstatic --noinput

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]