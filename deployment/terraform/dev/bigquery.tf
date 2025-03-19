resource "google_bigquery_dataset" "dev-study-helper-dataset" {
  dataset_id = "study_helper"
  project    = var.dev_project_id
  location   = var.region
  labels = {
    environment = "development"
  }
}

resource "google_bigquery_table" "dev-question-answer-table" {
  dataset_id = google_bigquery_dataset.prod-study-helper-dataset.dataset_id
  table_id   = "question_answer"
  project    = var.dev_project_id
  schema     = <<EOF
[
    {
        "name": "topic",
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
    }
]
EOF
}
