#!/usr/bin/env python3
"""
Delete Leads Script with Proper Foreign Key Constraint Handling

This script safely deletes leads and all their related records in the correct order
to avoid foreign key constraint violations.

Usage:
    python delete_leads.py 4                    # Delete lead ID 4
    python delete_leads.py 1,2,3,4             # Delete multiple leads
    python delete_leads.py --all               # Delete all leads
    python delete_leads.py 4 --dry-run         # Preview deletion
    python delete_leads.py 4 --no-confirm      # Skip confirmation
"""

import sys
import argparse
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Use raw SQL since we're connecting to remote staging database
# from models.database import get_db, engine, Base
# from models.lead import Lead
# from models.message import Message
# from models.agent_session import AgentSession
# from models.inbound_call import InboundCall


class LeadDeleter:
    """Handles safe deletion of leads with proper constraint handling"""

    def __init__(self, database_url: str = None):
        """Initialize with database connection"""
        if not database_url:
            # Try to get from environment variable, otherwise default to staging SQLite
            database_url = os.getenv('DATABASE_URL', 'sqlite:///./ailead-staging.db')

        self.engine = create_engine(database_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
        self.session.close()

    def get_lead_info(self, lead_id: int) -> dict:
        """Get comprehensive information about a lead and its related records"""
        try:
            # Get lead info with raw SQL
            lead_result = self.session.execute(
                text("SELECT id, name, email, phone, source, status, created_at FROM leads WHERE id = :lead_id"),
                {"lead_id": lead_id}
            ).fetchone()

            if not lead_result:
                return None

            # Count related records
            messages_count = self.session.execute(
                text("SELECT COUNT(*) FROM messages WHERE lead_id = :lead_id"),
                {"lead_id": lead_id}
            ).scalar() or 0

            sessions_count = self.session.execute(
                text("SELECT COUNT(*) FROM agent_sessions WHERE lead_id = :lead_id"),
                {"lead_id": lead_id}
            ).scalar() or 0

            calls_count = self.session.execute(
                text("SELECT COUNT(*) FROM inbound_calls WHERE lead_id = :lead_id"),
                {"lead_id": lead_id}
            ).scalar() or 0

            # Create a mock lead object
            class MockLead:
                def __init__(self, row):
                    self.id = row[0]
                    self.name = row[1]
                    self.email = row[2]
                    self.phone = row[3]
                    self.source = row[4]
                    self.status = row[5]
                    self.created_at = row[6]

            return {
                'lead': MockLead(lead_result),
                'messages_count': messages_count,
                'sessions_count': sessions_count,
                'calls_count': calls_count,
                'total_related': messages_count + sessions_count + calls_count
            }
        except Exception as e:
            print(f"❌ Error getting lead {lead_id} info: {e}")
            return None

    def preview_deletion(self, lead_ids: list) -> dict:
        """Preview what would be deleted without actually deleting"""
        preview = {
            'leads_to_delete': [],
            'leads_not_found': [],
            'total_related_records': 0
        }

        for lead_id in lead_ids:
            info = self.get_lead_info(lead_id)
            if info:
                preview['leads_to_delete'].append({
                    'id': lead_id,
                    'name': info['lead'].name or f"Lead {lead_id}",
                    'email': info['lead'].email,
                    'phone': info['lead'].phone,
                    'source': info['lead'].source,
                    'created_at': info['lead'].created_at,
                    'messages': info['messages_count'],
                    'sessions': info['sessions_count'],
                    'calls': info['calls_count'],
                    'total_related': info['total_related']
                })
                preview['total_related_records'] += info['total_related']
            else:
                preview['leads_not_found'].append(lead_id)

        return preview

    def delete_lead_safely(self, lead_id: int) -> dict:
        """Delete a single lead and all its related records safely"""
        result = {
            'success': False,
            'lead_id': lead_id,
            'deleted_records': {
                'messages': 0,
                'sessions': 0,
                'calls': 0,
                'lead': 0
            },
            'error': None
        }

        try:
            # Start transaction
            self.session.begin()

            print(f"🗑️  Deleting lead {lead_id} and related records...")

            # 1. Delete messages first (they reference lead_id)
            messages_result = self.session.execute(
                text("DELETE FROM messages WHERE lead_id = :lead_id"),
                {"lead_id": lead_id}
            )
            messages_deleted = messages_result.rowcount
            result['deleted_records']['messages'] = messages_deleted
            if messages_deleted > 0:
                print(f"   ✅ Deleted {messages_deleted} messages")

            # 2. Delete agent sessions
            sessions_result = self.session.execute(
                text("DELETE FROM agent_sessions WHERE lead_id = :lead_id"),
                {"lead_id": lead_id}
            )
            sessions_deleted = sessions_result.rowcount
            result['deleted_records']['sessions'] = sessions_deleted
            if sessions_deleted > 0:
                print(f"   ✅ Deleted {sessions_deleted} agent sessions")

            # 3. Delete inbound calls
            calls_result = self.session.execute(
                text("DELETE FROM inbound_calls WHERE lead_id = :lead_id"),
                {"lead_id": lead_id}
            )
            calls_deleted = calls_result.rowcount
            result['deleted_records']['calls'] = calls_deleted
            if calls_deleted > 0:
                print(f"   ✅ Deleted {calls_deleted} inbound calls")

            # 4. Finally delete the lead itself
            lead_result = self.session.execute(
                text("DELETE FROM leads WHERE id = :lead_id"),
                {"lead_id": lead_id}
            )
            lead_deleted = lead_result.rowcount
            result['deleted_records']['lead'] = lead_deleted

            if lead_deleted == 0:
                raise Exception(f"Lead {lead_id} not found")

            print(f"   ✅ Deleted lead {lead_id}")

            # Commit transaction
            self.session.commit()
            result['success'] = True

            total_deleted = sum(result['deleted_records'].values())
            print(f"   🎉 Successfully deleted {total_deleted} total records for lead {lead_id}")

        except Exception as e:
            # Rollback on error
            self.session.rollback()
            result['error'] = str(e)
            print(f"   ❌ Error deleting lead {lead_id}: {e}")

        return result

    def delete_leads(self, lead_ids: list) -> dict:
        """Delete multiple leads safely"""
        overall_result = {
            'success': True,
            'leads_processed': len(lead_ids),
            'leads_deleted': 0,
            'leads_failed': 0,
            'total_records_deleted': 0,
            'individual_results': [],
            'errors': []
        }

        for lead_id in lead_ids:
            result = self.delete_lead_safely(lead_id)
            overall_result['individual_results'].append(result)

            if result['success']:
                overall_result['leads_deleted'] += 1
                overall_result['total_records_deleted'] += sum(result['deleted_records'].values())
            else:
                overall_result['leads_failed'] += 1
                overall_result['errors'].append(f"Lead {lead_id}: {result['error']}")
                overall_result['success'] = False

        return overall_result

    def get_all_lead_ids(self) -> list:
        """Get all lead IDs in the database"""
        try:
            result = self.session.execute(text("SELECT id FROM leads ORDER BY id")).fetchall()
            return [row[0] for row in result]
        except Exception as e:
            print(f"❌ Error getting lead IDs: {e}")
            raise e


def parse_lead_ids(lead_ids_str: str) -> list:
    """Parse lead IDs from string (e.g., '1,2,3,4' -> [1,2,3,4])"""
    if not lead_ids_str:
        return []
    return [int(id.strip()) for id in lead_ids_str.split(',')]


def confirm_deletion(preview: dict) -> bool:
    """Ask user to confirm deletion"""
    print("\n" + "="*60)
    print("🚨 DELETION PREVIEW")
    print("="*60)

    if preview['leads_not_found']:
        print(f"❌ Leads not found: {preview['leads_not_found']}")

    if not preview['leads_to_delete']:
        print("❌ No valid leads to delete")
        return False

    print(f"📋 Found {len(preview['leads_to_delete'])} leads to delete:")
    print()

    for lead_info in preview['leads_to_delete']:
        print(f"🎯 Lead {lead_info['id']}: {lead_info['name']}")
        print(f"   📧 Email: {lead_info['email']}")
        print(f"   📞 Phone: {lead_info['phone']}")
        print(f"   📍 Source: {lead_info['source']}")
        print(f"   📅 Created: {lead_info['created_at']}")
        print(f"   🔗 Related records: {lead_info['messages']} messages, {lead_info['sessions']} sessions, {lead_info['calls']} calls")
        print()

    print(f"📊 Total related records to delete: {preview['total_related_records']}")
    print()
    print("⚠️  This action cannot be undone!")

    while True:
        response = input("\nProceed with deletion? (yes/no): ").lower().strip()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("Please enter 'yes' or 'no'")


def main():
    parser = argparse.ArgumentParser(
        description="Delete leads with proper foreign key constraint handling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python delete_leads.py 4                    # Delete lead ID 4
  python delete_leads.py 1,2,3,4             # Delete multiple leads
  python delete_leads.py --all               # Delete all leads
  python delete_leads.py 4 --dry-run         # Preview deletion
  python delete_leads.py 4 --no-confirm      # Skip confirmation
        """
    )

    parser.add_argument('lead_ids', nargs='?', help='Comma-separated lead IDs (e.g., 1,2,3) or single ID')
    parser.add_argument('--all', action='store_true', help='Delete all leads')
    parser.add_argument('--dry-run', action='store_true', help='Preview what would be deleted without deleting')
    parser.add_argument('--no-confirm', action='store_true', help='Skip confirmation prompt')
    parser.add_argument('--database-url', help='Custom database URL')

    args = parser.parse_args()

    # Validate arguments
    if not args.all and not args.lead_ids:
        parser.error("Must specify lead IDs or --all")

    if args.all and args.lead_ids:
        parser.error("Cannot specify both lead IDs and --all")

    print("🚀 Lead Deletion Script")
    print("=" * 50)

    try:
        with LeadDeleter(args.database_url) as deleter:
            # Determine which leads to process
            if args.all:
                lead_ids = deleter.get_all_lead_ids()
                print(f"📋 Found {len(lead_ids)} leads in database")
            else:
                lead_ids = parse_lead_ids(args.lead_ids)

            if not lead_ids:
                print("❌ No leads to process")
                return 1

            # Preview deletion
            preview = deleter.preview_deletion(lead_ids)

            if args.dry_run:
                print("\n🔍 DRY RUN - No actual deletion will occur")
                confirm_deletion(preview)
                print("\n✅ Dry run complete - no changes made")
                return 0

            # Confirm deletion unless skipped
            if not args.no_confirm:
                if not confirm_deletion(preview):
                    print("\n❌ Deletion cancelled by user")
                    return 0
            else:
                print(f"\n🚀 Deleting {len(preview['leads_to_delete'])} leads (confirmation skipped)")

            # Perform deletion
            print("\n" + "="*60)
            print("🗑️  STARTING DELETION")
            print("="*60)

            start_time = datetime.now()
            result = deleter.delete_leads([info['id'] for info in preview['leads_to_delete']])
            end_time = datetime.now()

            # Print results
            print("\n" + "="*60)
            print("📊 DELETION RESULTS")
            print("="*60)

            print(f"⏱️  Time taken: {(end_time - start_time).total_seconds():.2f} seconds")
            print(f"📋 Leads processed: {result['leads_processed']}")
            print(f"✅ Leads deleted: {result['leads_deleted']}")
            print(f"❌ Leads failed: {result['leads_failed']}")
            print(f"🗑️  Total records deleted: {result['total_records_deleted']}")

            if result['errors']:
                print(f"\n❌ Errors:")
                for error in result['errors']:
                    print(f"   {error}")

            if result['success']:
                print(f"\n🎉 All leads deleted successfully!")
                return 0
            else:
                print(f"\n⚠️  Some deletions failed")
                return 1

    except Exception as e:
        print(f"\n❌ Script error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())