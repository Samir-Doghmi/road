library(DBI)
library(RPostgres)

# Establish connection using environment variables
con <- dbConnect(
  RPostgres::Postgres(),
  host     = Sys.getenv("POSTGRES_HOST", "postgres"),
  dbname   = Sys.getenv("POSTGRES_DB", "road"),
  user     = Sys.getenv("POSTGRES_USER", "postgres"),
  password = Sys.getenv("POSTGRES_PASSWORD", "password"),
  port     = as.integer(Sys.getenv("POSTGRES_PORT", 5432))
)

# Query data
df <- dbGetQuery(con, "SELECT * FROM measurements LIMIT 10;")
print(df)

# Always disconnect when done
dbDisconnect(con)
