# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

resource "google_storage_bucket" "bucket_load_test_results" {
  name                        = "${var.cicd_runner_project_id}-${var.suffix_bucket_name_load_test_results}"
  location                    = var.region
  project                     = var.cicd_runner_project_id
  uniform_bucket_level_access = true
  force_destroy               = true
  depends_on                  = [resource.google_project_service.cicd_services, resource.google_project_service.shared_services]
}

resource "google_storage_bucket" "logs_data_bucket" {
  for_each                    = toset(local.all_project_ids)
  name                        = "${each.value}-logs-data"
  location                    = var.region
  project                     = each.value
  uniform_bucket_level_access = true
  force_destroy               = true

  depends_on = [resource.google_project_service.cicd_services, resource.google_project_service.shared_services]
}

resource "google_storage_bucket" "knowledge_bucket_staging" {
  project  = var.staging_project_id
  name     = "${var.staging_project_id}-knowledge-bucket"
  location = var.data_store_region
}

resource "google_storage_bucket" "knowledge_bucket_prod" {
  project  = var.prod_project_id
  name     = "${var.prod_project_id}-knowledge-bucket"
  location = var.data_store_region
}

resource "google_discovery_engine_data_store" "data_store_staging" {
  location          = var.data_store_region
  project           = var.staging_project_id
  data_store_id     = var.datastore_name
  display_name      = var.datastore_name
  industry_vertical = "GENERIC"
  content_config    = "CONTENT_REQUIRED"
  solution_types    = ["SOLUTION_TYPE_SEARCH"]
  document_processing_config {
    default_parsing_config {
      digital_parsing_config {}
    }
  }
  provider   = google.staging_billing_override
  depends_on = [resource.google_project_service.cicd_services, resource.google_project_service.shared_services]
}

resource "google_discovery_engine_search_engine" "search_engine_staging" {
  project        = var.staging_project_id
  engine_id      = var.search_engine_name
  collection_id  = "default_collection"
  location       = google_discovery_engine_data_store.data_store_staging.location
  display_name   = "Search Engine App Staging"
  data_store_ids = [google_discovery_engine_data_store.data_store_staging.data_store_id]
  search_engine_config {
    search_tier = "SEARCH_TIER_ENTERPRISE"
  }
  provider = google.staging_billing_override
}

resource "google_discovery_engine_data_store" "data_store_prod" {
  location          = var.data_store_region
  project           = var.prod_project_id
  data_store_id     = var.datastore_name
  display_name      = var.datastore_name
  industry_vertical = "GENERIC"
  content_config    = "CONTENT_REQUIRED"
  solution_types    = ["SOLUTION_TYPE_SEARCH"]
  document_processing_config {
    default_parsing_config {
      digital_parsing_config {}
    }
  }
  provider   = google.prod_billing_override
  depends_on = [resource.google_project_service.cicd_services, resource.google_project_service.shared_services]
}

resource "google_discovery_engine_search_engine" "search_engine_prod" {
  project        = var.prod_project_id
  engine_id      = var.search_engine_name
  collection_id  = "default_collection"
  location       = google_discovery_engine_data_store.data_store_prod.location
  display_name   = "Search Engine App Prod"
  data_store_ids = [google_discovery_engine_data_store.data_store_prod.data_store_id]
  search_engine_config {
    search_tier = "SEARCH_TIER_ENTERPRISE"
  }
  provider = google.prod_billing_override
}
