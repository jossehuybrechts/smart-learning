resource "google_storage_bucket" "cf_source_bucket" {
  for_each                    = local.deploy_project_ids
  project                     = each.value
  name                        = "${each.value}-gcf-source-bucket"
  location                    = "EU"
  uniform_bucket_level_access = true
}

data "archive_file" "default" {
  type        = "zip"
  output_path = "/tmp/function-source.zip"
  source_dir  = "../../cloud_function/"
}

resource "google_storage_bucket_object" "default" {
  for_each = local.deploy_project_ids
  name     = "function-source.zip"
  bucket   = google_storage_bucket.cf_source_bucket[each.key].name
  source   = data.archive_file.default.output_path # Path to the zipped function source code
}

data "google_storage_project_service_account" "default" {
  for_each = local.deploy_project_ids
  project  = each.value
}

resource "google_project_iam_member" "gcs_pubsub_publishing" {
  for_each = local.deploy_project_ids
  project  = each.value
  role     = "roles/pubsub.publisher"
  member   = "serviceAccount:${data.google_storage_project_service_account.default[each.key].email_address}"
}

resource "google_service_account" "cf_sa" {
  for_each     = local.deploy_project_ids
  account_id   = "gcf-sa-${each.key}"
  project      = each.value
  display_name = "Service Account - used for both the cloud function and eventarc trigger"
}

# Permissions on the service account used by the function and Eventarc trigger
resource "google_project_iam_member" "invoking" {
  for_each   = local.deploy_project_ids
  project    = each.value
  role       = "roles/run.invoker"
  member     = "serviceAccount:${google_service_account.cf_sa[each.key].email}"
  depends_on = [google_project_iam_member.gcs_pubsub_publishing]
}

resource "google_project_iam_member" "event_receiving" {
  for_each   = local.deploy_project_ids
  project    = each.value
  role       = "roles/eventarc.eventReceiver"
  member     = "serviceAccount:${google_service_account.cf_sa[each.key].email}"
  depends_on = [google_project_iam_member.invoking]
}

resource "google_project_iam_member" "artifactregistry_reader" {
  for_each   = local.deploy_project_ids
  project    = each.value
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${google_service_account.cf_sa[each.key].email}"
  depends_on = [google_project_iam_member.event_receiving]
}

resource "google_project_iam_member" "aiplatform_user" {
  for_each   = local.deploy_project_ids
  project    = each.value
  role       = "roles/aiplatform.user"
  member     = "serviceAccount:${google_service_account.cf_sa[each.key].email}"
  depends_on = [google_project_iam_member.event_receiving]
}

resource "google_service_account" "build_sa" {
  for_each     = local.deploy_project_ids
  account_id   = "build-sa-${each.key}"
  project      = each.value
  display_name = "Service Account - used for the cloud function build"
}

resource "google_project_iam_member" "log_writer" {
  for_each = local.deploy_project_ids
  project  = each.value
  role     = "roles/logging.logWriter"
  member   = "serviceAccount:${google_service_account.build_sa[each.key].email}"
}

resource "google_project_iam_member" "ar_writer" {
  for_each = local.deploy_project_ids
  project  = each.value
  role     = "roles/artifactregistry.writer"
  member   = "serviceAccount:${google_service_account.build_sa[each.key].email}"
}

resource "google_project_iam_member" "object_viewer" {
  for_each = local.deploy_project_ids
  project  = each.value
  role     = "roles/storage.objectViewer"
  member   = "serviceAccount:${google_service_account.build_sa[each.key].email}"
}

resource "google_cloudfunctions2_function" "staging_function" {
  project = var.staging_project_id
  depends_on = [
    google_project_iam_member.event_receiving,
    google_project_iam_member.artifactregistry_reader,
  ]
  name        = "staging-rag-import-function"
  location    = var.region
  description = "Staging Function for importing docuemnts to the Discovery Engine Data Store"

  build_config {
    runtime     = "python312"
    entry_point = "main" # Set the entry point in the code
    source {
      storage_source {
        bucket = google_storage_bucket.cf_source_bucket["staging"].name
        object = google_storage_bucket_object.default["staging"].name
      }
    }
    service_account = google_service_account.build_sa["staging"].id
  }

  service_config {
    max_instance_count = 3
    available_memory   = "512M"
    timeout_seconds    = 180
    environment_variables = {
      RAG_CORPUS_NAME = var.rag_cropus_name
    }
    ingress_settings               = "ALLOW_INTERNAL_ONLY"
    all_traffic_on_latest_revision = true
    service_account_email          = google_service_account.cf_sa["staging"].email
  }

  event_trigger {
    trigger_region        = var.region # The trigger must be in the same location as the bucket
    event_type            = "google.cloud.storage.object.v1.finalized"
    retry_policy          = "RETRY_POLICY_RETRY"
    service_account_email = google_service_account.cf_sa["staging"].email
    event_filters {
      attribute = "bucket"
      value     = google_storage_bucket.knowledge_bucket["staging"].name
    }
  }

  lifecycle {
    ignore_changes = [
      build_config[0].source,
    ]
  }
}

resource "google_cloudfunctions2_function" "prod_function" {
  project = var.prod_project_id
  depends_on = [
    google_project_iam_member.event_receiving,
    google_project_iam_member.artifactregistry_reader,
  ]
  name        = "prod-rag-import-function"
  location    = var.region
  description = "Prod Function for importing docuemnts to the RAG Engine"

  build_config {
    runtime     = "python312"
    entry_point = "main" # Set the entry point in the code
    source {
      storage_source {
        bucket = google_storage_bucket.cf_source_bucket["prod"].name
        object = google_storage_bucket_object.default["prod"].name
      }
    }
    service_account = google_service_account.build_sa["prod"].id
  }

  service_config {
    max_instance_count = 3
    available_memory   = "512M"
    timeout_seconds    = 180
    environment_variables = {
      RAG_CORPUS_NAME = var.rag_cropus_name
    }
    ingress_settings               = "ALLOW_INTERNAL_ONLY"
    all_traffic_on_latest_revision = true
    service_account_email          = google_service_account.cf_sa["prod"].email
  }

  event_trigger {
    trigger_region        = var.region # The trigger must be in the same location as the bucket
    event_type            = "google.cloud.storage.object.v1.finalized"
    retry_policy          = "RETRY_POLICY_RETRY"
    service_account_email = google_service_account.cf_sa["prod"].email
    event_filters {
      attribute = "bucket"
      value     = google_storage_bucket.knowledge_bucket["prod"].name
    }
  }

  lifecycle {
    ignore_changes = [
      build_config[0].source,
    ]
  }
}
