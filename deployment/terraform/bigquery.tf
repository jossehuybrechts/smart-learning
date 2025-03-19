resource "google_bigquery_dataset" "prod-study-helper-dataset" {
  dataset_id = "study_helper"
  project    = var.prod_project_id
  location   = var.region
  labels = {
    environment = "production"
  }
}

resource "google_bigquery_table" "prod-question-answer-table" {
  dataset_id = google_bigquery_dataset.prod-study-helper-dataset.dataset_id
  table_id   = "question_answer"
  project    = var.prod_project_id
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
resource "google_bigquery_dataset" "staging-study-helper-dataset" {
  dataset_id = "study_helper"
  project    = var.staging_project_id
  location   = var.region
  labels = {
    environment = "staging"
  }
}


resource "google_bigquery_table" "staging-question-answer-table" {
  dataset_id = google_bigquery_dataset.staging-study-helper-dataset.dataset_id
  table_id   = "question_answer"
  project    = var.staging_project_id
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
