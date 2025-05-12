resource "google_bigquery_dataset" "dev-study-helper-dataset" {
  dataset_id = "study_helper"
  project    = var.dev_project_id
  location   = var.region
  labels = {
    environment = "development"
  }
  depends_on = [resource.google_project_service.services]
}

resource "google_bigquery_table" "dev-question-answer-table" {
  dataset_id = google_bigquery_dataset.dev-study-helper-dataset.dataset_id
  table_id   = "question_answer"
  project    = var.dev_project_id
  schema     = <<EOF
[
    {
        "name": "userId",
        "type": "STRING",
        "mode": "REQUIRED"
    },
    {
        "name": "sessionId",
        "type": "STRING",
        "mode": "REQUIRED"
    },
    {
        "name": "subject",
        "type": "STRING",
        "mode": "REQUIRED"
    },
    {
        "name": "chapter",
        "type": "STRING",
        "mode": "REQUIRED"
    },
    {
        "name": "question",
        "type": "STRING",
        "mode": "REQUIRED"
    },
    {
        "name": "answer",
        "type": "STRING",
        "mode": "REQUIRED"
    },
    {
        "name": "student_score",
        "type": "INTEGER",
        "mode": "REQUIRED"
    },
    {
        "name": "max_score",
        "type": "INTEGER",
        "mode": "REQUIRED"
    },
    {
        "name": "difficulty",
        "type": "INTEGER",
        "mode": "REQUIRED"
    },
    {
        "name": "timestamp",
        "type": "TIMESTAMP",
        "mode": "REQUIRED"
    }
]
EOF
  depends_on = [resource.google_project_service.services]
}
