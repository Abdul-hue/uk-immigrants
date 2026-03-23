from db.connection import get_connection
from db.seeds.appendices import seed_appendices
from db.seeds.question_sequences import seed_question_sequences
from db.seeds.visitor_questions import seed_visitor_questions

def seed_all():
    """Run all seed scripts in the correct dependency order."""
    conn = get_connection()
    try:
        print("Starting master seed process...")
        
        # 1. Appendices (Parent Table)
        print("Step 1/3: Seeding appendices...")
        app_count = seed_appendices(conn)
        print(f"  Done: {app_count} appendices seeded.")
        
        # 2. Question Sequences (Depends on appendices)
        print("Step 2/3: Seeding question sequences...")
        qs_result = seed_question_sequences(conn)
        print(f"  Done: {qs_result['total']} questions seeded.")
        
        # 3. Visitor Questions (Depends on appendices)
        print("Step 3/3: Seeding visitor questions...")
        vis_count = seed_visitor_questions(conn)
        print(f"  Done: {vis_count} visitor questions seeded.")
        
        print("\nMaster seed process completed successfully! ✅")
        
    except Exception as e:
        print(f"\nError during master seed process: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    seed_all()
