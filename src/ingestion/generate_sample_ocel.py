from pathlib import Path

import pandas as pd
from pm4py.objects.ocel.obj import OCEL


def build_p2p_ocel() -> OCEL:
    """
    Build a small P2P (Procure-to-Pay) object-centric event log.

    Returns:
        OCEL object constructed from events, objects, and relations tables.
    """

    # --------------------------------------------------
    # 1. EVENTS TABLE
    # Each row represents an event (activity execution)
    # --------------------------------------------------
    events = pd.DataFrame([
        {"ocel:eid": "e1", "ocel:activity": "Create Purchase Order", "ocel:timestamp": "2026-04-01 09:00:00"},
        {"ocel:eid": "e2", "ocel:activity": "Approve Purchase Order", "ocel:timestamp": "2026-04-01 10:00:00"},
        {"ocel:eid": "e3", "ocel:activity": "Send Purchase Order", "ocel:timestamp": "2026-04-01 11:00:00"},
        {"ocel:eid": "e4", "ocel:activity": "Receive Goods", "ocel:timestamp": "2026-04-02 09:00:00"},
        {"ocel:eid": "e5", "ocel:activity": "Record Goods Receipt", "ocel:timestamp": "2026-04-02 10:00:00"},
        {"ocel:eid": "e6", "ocel:activity": "Receive Invoice", "ocel:timestamp": "2026-04-03 09:00:00"},
        {"ocel:eid": "e7", "ocel:activity": "Match Invoice", "ocel:timestamp": "2026-04-03 11:00:00"},
        {"ocel:eid": "e8", "ocel:activity": "Pay Invoice", "ocel:timestamp": "2026-04-04 15:00:00"},
    ])

    # --------------------------------------------------
    # 2. OBJECTS TABLE
    # Each row represents a business object in the process
    # --------------------------------------------------
    objects = pd.DataFrame([
        {"ocel:oid": "po1", "ocel:type": "purchase_order"},
        {"ocel:oid": "item1", "ocel:type": "item"},
        {"ocel:oid": "gr1", "ocel:type": "goods_receipt"},
        {"ocel:oid": "inv1", "ocel:type": "invoice"},
    ])

    # --------------------------------------------------
    # 3. RELATIONS TABLE
    # Defines which event is related to which object
    # This is the core of object-centric modeling
    # --------------------------------------------------
    relations = pd.DataFrame([
        # Purchase Order lifecycle
        {"ocel:eid": "e1", "ocel:oid": "po1", "ocel:type": "purchase_order"},
        {"ocel:eid": "e2", "ocel:oid": "po1", "ocel:type": "purchase_order"},
        {"ocel:eid": "e3", "ocel:oid": "po1", "ocel:type": "purchase_order"},

        # Goods receipt linked to PO and item
        {"ocel:eid": "e4", "ocel:oid": "po1", "ocel:type": "purchase_order"},
        {"ocel:eid": "e4", "ocel:oid": "item1", "ocel:type": "item"},

        # Recording goods receipt linked to GR and PO
        {"ocel:eid": "e5", "ocel:oid": "gr1", "ocel:type": "goods_receipt"},
        {"ocel:eid": "e5", "ocel:oid": "po1", "ocel:type": "purchase_order"},

        # Invoice lifecycle
        {"ocel:eid": "e6", "ocel:oid": "inv1", "ocel:type": "invoice"},

        # Matching invoice with PO
        {"ocel:eid": "e7", "ocel:oid": "po1", "ocel:type": "purchase_order"},
        {"ocel:eid": "e7", "ocel:oid": "inv1", "ocel:type": "invoice"},

        # Payment linked only to invoice
        {"ocel:eid": "e8", "ocel:oid": "inv1", "ocel:type": "invoice"},
    ])

    # --------------------------------------------------
    # Convert timestamps to proper datetime format
    # --------------------------------------------------
    events["ocel:timestamp"] = pd.to_datetime(events["ocel:timestamp"])

    # --------------------------------------------------
    # Create OCEL object from the three tables
    # --------------------------------------------------
    ocel = OCEL(events=events, objects=objects, relations=relations)

    return ocel


def save_p2p_ocel(base_path: str = "data/p2p_sample") -> None:
    """
    Save the generated OCEL tables as CSV files.

    Args:
        base_path: Directory where the CSV files will be stored
    """

    # Create output directory if it does not exist
    output_dir = Path(base_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build OCEL object
    ocel = build_p2p_ocel()

    # --------------------------------------------------
    # Save each table separately for transparency/debugging
    # --------------------------------------------------
    ocel.events.to_csv(output_dir / "events.csv", index=False)
    ocel.objects.to_csv(output_dir / "objects.csv", index=False)
    ocel.relations.to_csv(output_dir / "relations.csv", index=False)

    print("P2P OCEL generated and saved.")
    print(f"Location: {output_dir}")


# --------------------------------------------------
# Entry point: run this file directly to generate data
# --------------------------------------------------
if __name__ == "__main__":
    save_p2p_ocel()
