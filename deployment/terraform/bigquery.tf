resource "google_bigquery_dataset" "prod-study-helper-dataset" {
  dataset_id = "study_helper"
  project    = var.prod_project_id
  location   = var.region
  labels = {
    environment = "production"
  }
  depends_on = [resource.google_project_service.cicd_services, resource.google_project_service.shared_services]
}

resource "google_bigquery_table" "prod-question-answer-table" {
  dataset_id = google_bigquery_dataset.prod-study-helper-dataset.dataset_id
  table_id   = "question_answer"
  project    = var.prod_project_id
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
  depends_on = [resource.google_project_service.cicd_services, resource.google_project_service.shared_services]
}

resource "google_bigquery_dataset" "staging-study-helper-dataset" {
  dataset_id = "study_helper"
  project    = var.staging_project_id
  location   = var.region
  labels = {
    environment = "staging"
  }
  depends_on = [resource.google_project_service.cicd_services, resource.google_project_service.shared_services]
}

resource "google_bigquery_table" "staging-question-answer-table" {
  dataset_id = google_bigquery_dataset.staging-study-helper-dataset.dataset_id
  table_id   = "question_answer"
  project    = var.staging_project_id
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
  depends_on = [resource.google_project_service.cicd_services, resource.google_project_service.shared_services]
}
