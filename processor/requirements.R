# requirements.R

install_if_missing <- function(p) {
  if (!requireNamespace(p, quietly = TRUE)) {
    install.packages(p, repos = "https://cloud.r-project.org")
  }
}

install_if_missing("DBI")
install_if_missing("RPostgres")
install_if_missing("dplyr")
