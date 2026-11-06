FROM python:3.13-slim

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Collect the admin page CSS so the server can serve it
RUN SECRET_KEY=build DATABASE_URL=sqlite:// python web/manage.py collectstatic --noinput

EXPOSE 8000

# run the database migration first, then start the server on the port the host gives it, or 8000 if none is given
CMD ["sh", "-c", "python web/manage.py migrate && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]