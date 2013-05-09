Aeroback
========
Backup/migrate your data to Amazon S3/Google Storage
----------------------------------------------------
Backup or move your server data or desktop files to Amazon S3 or Google Storage. This Python 2.7 script is easily configurable and supports compressed and incremental directory backup/migration to cloud storages.

Why this script?
----------------
My server has accumulated a lot of Gb of data that I needed to store long term. However, the problem was my server's monthly bandwidth allowance which I couldn't exceed. 
Aeroback migrates data in installments that you control. This allows for gradual transition to the cloud storage while keeping your server running and receiving new data.

###Main features:
* Set limit of upload amount per session
* Several machines can store to same bucket
* Easily configurable via simple .ini file
* Recognizes machine it is being run on
* Emails detailed report when done (optional)

###Supported backup types:
* Incremental directories with includes/excludes and max upload limit
* Compressed directories with history of N versions
* Database backup (MongoDB and MySQL) with history on N versions

###Supported cloud storages:
* Amazon S3
* Google Storage

###Incremental Files Backup
This is the main cause of writing this script. Specify a directory, its optional include/exclude subdirectories and set a limit of upload per session.
For example:
```ini
[backup_dir_increment]
    active = true
    dirstorage = data/sound
    dir = /home/alex/data/sound
    maxupload = 1g
    includes =
    excludes = 
          work/temp
          cache
    description = Audio files
```

###Compressed Directory Backup
A single directory or multpiple directories gets compressed and time stamp added. Handy for keeping a history of multiple versions.
For example:
```
[backup_dir_compress]         
    active = true
    dirstorage = emails
    history = 10
    dirs =  
          /home/alex/emails/in
          /home/alex/emails/out
    description = 
```

###Mongo DB Backup
Data base dump that is compressed and time stamp added. Also supports for a history of versions. Currently dumps ALL tables.
For example:
```
[backup_db_mongo]             
   active = true
   dirstorage = db/mongo
   history = 5
   user = 
   password =
   host = 127.0.0.1
   description = DB Mongo backup
```

###MySQL DB Backup
Data base dump that is compressed and time stamp added. Also supports for a history of versions. Currently dumps ALL tables.
For example:
```
[backup_db_mysql]
   active = true
   dirstorage = db/mysql
   history = 8
   user = 
   password =
   host = 127.0.0.1
   description = DB MySQL backup
```

###Dependencies:
Only one `gsutil` to access Amazon S3 and Google Storage. Read [gsutil project page](https://developers.google.com/storage/docs/gsutil) for more details.

How to Install
--------------
More to come...

How to Configure
----------------
More to come...

How to Run
----------
More to come...
