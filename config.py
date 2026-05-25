import os
# The following are optimized for running the tests.
# But you also can use hard-coded absolute paths depending on your system.
path_base = os.getcwd()
path_data_processed = os.path.join(path_base, 'data_raw')
path_data_processed = os.path.join(path_base, 'data_processed')
path_data_pickled = os.path.join(path_base, 'test')
database_name = "sunshine"
database_user = "xxx"
database_password = "xxx"
database_port = 5432 # postgresql
database_host = "192.168.1.1"
tracker_mask = []
is_testing = 1 # If set, just do database requests in dry-run.