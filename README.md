##Read Town Post
Orphaned files are physical image files sitting in your media/ folder on your hard drive that no longer have a matching record in your database.
They usually happen when:
You delete a post from the admin panel (Django deletes the database row, but leaves the physical file behind for safety).
A user starts an upload but closes the browser before submitting the form, leaving a stray file on the server.
When you run:
python manage.py cleanup_orphaned_images
It will safely scan your media/ folder, compare it to your database, and just list the orphaned files without deleting anything. It's completely safe to run anytime you want to check your disk space!
python manage.py cleanup_orphaned_images
python manage.py cleanup_orphaned_images --delete --days-old 30