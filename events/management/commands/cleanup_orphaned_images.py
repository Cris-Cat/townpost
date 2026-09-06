import os
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from events.models import EventImage

class Command(BaseCommand):
    help = 'Finds and optionally deletes orphaned image files not referenced in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Actually delete the orphaned files (dry run by default)',
        )
        parser.add_argument(
            '--days-old',
            type=int,
            default=0,
            help='Only delete files older than X days (default: 0 = all files)',
        )

    def handle(self, *args, **options):
        media_root = Path(settings.MEDIA_ROOT)
        images_dir = media_root / 'event_images'
        
        if not images_dir.exists():
            self.stdout.write(self.style.WARNING(f"Images directory not found: {images_dir}"))
            return

        # Get all image files currently in the database
        db_files = set()
        for img_obj in EventImage.objects.all():
            # Extract just the relative path from the ImageField
            if img_obj.image:
                db_files.add(str(img_obj.image.name))

        # Find all actual files on disk
        orphaned_files = []
        total_size = 0
        
        for root, dirs, files in os.walk(images_dir):
            for file in files:
                # Skip hidden files and system files
                if file.startswith('.') or file.endswith('.pyc'):
                    continue
                    
                file_path = Path(root) / file
                relative_path = str(file_path.relative_to(media_root))
                
                # Check if this file is referenced in the database
                if relative_path not in db_files:
                    file_size = file_path.stat().st_size
                    file_mtime = file_path.stat().st_mtime
                    
                    orphaned_files.append({
                        'path': relative_path,
                        'size': file_size,
                        'size_mb': file_size / (1024 * 1024),
                        'mtime': file_mtime,
                    })
                    total_size += file_size

        # Summary
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"ORPHANED IMAGES CLEANUP REPORT")
        self.stdout.write(f"{'='*60}\n")
        self.stdout.write(f"Total orphaned files found: {len(orphaned_files)}")
        self.stdout.write(f"Total disk space used: {total_size / (1024 * 1024):.2f} MB\n")

        if not orphaned_files:
            self.stdout.write(self.style.SUCCESS("No orphaned files found. Your media folder is clean!"))
            return

        # Show files
        self.stdout.write("\nOrphaned files:")
        self.stdout.write("-" * 60)
        for i, file_info in enumerate(orphaned_files[:20], 1):  # Show first 20
            self.stdout.write(f"{i}. {file_info['path']} ({file_info['size_mb']:.2f} MB)")
        
        if len(orphaned_files) > 20:
            self.stdout.write(f"\n... and {len(orphaned_files) - 20} more files")

        # Delete if requested
        if options['delete']:
            days_old = options['days_old']
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(self.style.WARNING("DELETION MODE ACTIVATED"))
            self.stdout.write(f"{'='*60}\n")
            
            confirm = input(f"\nAre you sure you want to delete {len(orphaned_files)} orphaned files? (yes/no): ")
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.SUCCESS("Deletion cancelled."))
                return

            deleted_count = 0
            deleted_size = 0
            
            for file_info in orphaned_files:
                file_path = media_root / file_info['path']
                
                # Check age filter if specified
                if days_old > 0:
                    import time
                    file_age_days = (time.time() - file_info['mtime']) / (60 * 60 * 24)
                    if file_age_days < days_old:
                        continue
                
                try:
                    file_size = file_path.stat().st_size
                    file_path.unlink()  # Delete the file
                    deleted_count += 1
                    deleted_size += file_size
                    self.stdout.write(f"✓ Deleted: {file_info['path']}")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"✗ Failed to delete {file_info['path']}: {e}"))

            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(self.style.SUCCESS(f"CLEANUP COMPLETE"))
            self.stdout.write(f"{'='*60}")
            self.stdout.write(f"Files deleted: {deleted_count}")
            self.stdout.write(f"Space freed: {deleted_size / (1024 * 1024):.2f} MB")
            
        else:
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(self.style.WARNING("DRY RUN MODE"))
            self.stdout.write(f"{'='*60}")
            self.stdout.write("\nTo actually delete these files, run:")
            self.stdout.write(self.style.SUCCESS("python manage.py cleanup_orphaned_images --delete"))
            self.stdout.write("\nTo only delete files older than X days:")
            self.stdout.write(self.style.SUCCESS("python manage.py cleanup_orphaned_images --delete --days-old 30"))