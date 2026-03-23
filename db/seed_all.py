from db.connection import get_connection
from db.seeds.appendices import seed_appendices
from db.seeds.question_sequences import seed_question_sequences
from db.seeds.visitor_questions import seed_visitor_questions
from db.seeds.hard_gates import seed_hard_gates

def seed_all():
    """Run all seed scripts in the correct dependency order."""
    conn = get_connection()
    try:
        print("Starting master seed process...")
        
        # 1. Appendices (Parent Table)
        print("Step 1/4: Seeding appendices...")
        app_count = seed_appendices(conn)
        print(f"  Done: {app_count} appendices seeded.")
        
        # 2. Hard Gates (Static Definitions)
        print("Step 2/4: Seeding hard gates...")
        hg_count = seed_hard_gates(conn)
        print(f"  Done: {hg_count} hard gates seeded.")
        
        # 3. Question Sequences (Depends on appendices)
        print("Step 3/4: Seeding question sequences...")
        qs_result = seed_question_sequences(conn)
        print(f"  Done: {qs_result['total']} questions seeded.")
        
        # 4. Visitor Questions (Depends on appendices)
        print("Step 4/4: Seeding visitor questions...")
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
