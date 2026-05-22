from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
from pm4py.objects.ocel.obj import OCEL


EVENT_ID = "ocel:eid"
ACTIVITY = "ocel:activity"
TIMESTAMP = "ocel:timestamp"
OBJECT_ID = "ocel:oid"
OBJECT_TYPE = "ocel:type"
QUALIFIER = "ocel:qualifier"


def build_master_data(
    supplier_count: int = 50,
    product_count: int = 200,
    cost_center_count: int = 20,
) -> dict[str, pd.DataFrame]:
    suppliers = pd.DataFrame(
        [
            {
                "supplier_id": f"supplier_{i:03d}",
                "supplier_name": f"Supplier {i:03d}",
                "supplier_region": random.choice(["EU", "UK", "US", "APAC"]),
                "risk_level": random.choice(["low", "medium", "high"]),
            }
            for i in range(1, supplier_count + 1)
        ]
    )

    products = pd.DataFrame(
        [
            {
                "product_id": f"product_{i:04d}",
                "product_name": f"Product {i:04d}",
                "product_category": random.choice(
                    ["IT Hardware", "Office Supplies", "Logistics", "Maintenance", "Services"]
                ),
                "unit_price": round(random.uniform(10, 1500), 2),
            }
            for i in range(1, product_count + 1)
        ]
    )

    cost_centers = pd.DataFrame(
        [
            {
                "cost_center_id": f"cc_{i:03d}",
                "cost_center_name": f"Cost Center {i:03d}",
                "business_unit": random.choice(
                    ["Operations", "Finance", "IT", "Procurement", "Sales"]
                ),
            }
            for i in range(1, cost_center_count + 1)
        ]
    )

    return {
        "suppliers": suppliers,
        "products": products,
        "cost_centers": cost_centers,
    }


def add_object(
    objects: list[dict[str, str]],
    object_id: str,
    object_type: str,
    seen_objects: set[tuple[str, str]],
) -> None:
    key = (object_id, object_type)

    if key not in seen_objects:
        objects.append({
            OBJECT_ID: object_id,
            OBJECT_TYPE: object_type,
        })
        seen_objects.add(key)


def add_event(
    events: list[dict[str, Any]],
    relations: list[dict[str, str]],
    event_id: str,
    activity: str,
    timestamp: datetime,
    related_objects: list[tuple[str, str, str]],
) -> None:
    events.append({
        EVENT_ID: event_id,
        ACTIVITY: activity,
        TIMESTAMP: timestamp,
    })

    for object_id, object_type, qualifier in related_objects:
        relations.append({
            EVENT_ID: event_id,
            OBJECT_ID: object_id,
            OBJECT_TYPE: object_type,
            QUALIFIER: qualifier,
        })


def build_p2p_ocel(
    purchase_order_count: int = 2000,
    seed: int = 42,
) -> OCEL:
    """
    Build a synthetic enterprise-like P2P object-centric event log.

    The goal is not to perfectly simulate a real company.
    The goal is to create realistic enough process behavior for analytics,
    automation discovery, and AI advisory demos.

    Generated behavior includes:
    - happy path purchase orders
    - approval rework
    - partial deliveries
    - invoice mismatch
    - delayed approvals
    - delayed invoice matching
    - multiple object types
    - optional master-data-style business objects
    """

    random.seed(seed)

    master_data = build_master_data()
    suppliers = master_data["suppliers"]
    products = master_data["products"]
    cost_centers = master_data["cost_centers"]

    events: list[dict[str, Any]] = []
    objects: list[dict[str, str]] = []
    relations: list[dict[str, str]] = []
    seen_objects: set[tuple[str, str]] = set()

    base_timestamp = datetime(2026, 1, 1, 8, 0, 0)
    event_counter = 1

    for po_index in range(1, purchase_order_count + 1):
        po_id = f"po_{po_index:06d}"
        supplier = suppliers.sample(1).iloc[0]
        cost_center = cost_centers.sample(1).iloc[0]

        supplier_id = supplier["supplier_id"]
        cost_center_id = cost_center["cost_center_id"]

        item_count = random.randint(1, 5)
        invoice_count = 1 if random.random() < 0.85 else 2

        has_approval_rework = random.random() < 0.12
        has_invoice_mismatch = random.random() < 0.18
        has_partial_delivery = random.random() < 0.20
        has_slow_approval = random.random() < 0.15
        has_slow_invoice_matching = random.random() < 0.20

        timestamp = base_timestamp + timedelta(
            minutes=random.randint(0, purchase_order_count * 3)
        )

        add_object(objects, po_id, "purchase_order", seen_objects)
        add_object(objects, supplier_id, "supplier", seen_objects)
        add_object(objects, cost_center_id, "cost_center", seen_objects)

        item_ids: list[str] = []

        for item_index in range(1, item_count + 1):
            item_id = f"{po_id}_item_{item_index}"
            product = products.sample(1).iloc[0]
            product_id = product["product_id"]

            item_ids.append(item_id)

            add_object(objects, item_id, "item", seen_objects)
            add_object(objects, product_id, "product", seen_objects)

        def next_event_id() -> str:
            nonlocal event_counter
            event_id = f"e_{event_counter:09d}"
            event_counter += 1
            return event_id

        add_event(
            events=events,
            relations=relations,
            event_id=next_event_id(),
            activity="Create Purchase Order",
            timestamp=timestamp,
            related_objects=[
                (po_id, "purchase_order", "primary"),
                (supplier_id, "supplier", "reference"),
                (cost_center_id, "cost_center", "reference"),
            ],
        )

        timestamp += timedelta(hours=random.randint(1, 8))

        if has_slow_approval:
            timestamp += timedelta(days=random.randint(2, 6))

        if has_approval_rework:
            add_event(
                events=events,
                relations=relations,
                event_id=next_event_id(),
                activity="Request Purchase Order Change",
                timestamp=timestamp,
                related_objects=[
                    (po_id, "purchase_order", "primary"),
                    (cost_center_id, "cost_center", "reference"),
                ],
            )

            timestamp += timedelta(hours=random.randint(2, 12))

            add_event(
                events=events,
                relations=relations,
                event_id=next_event_id(),
                activity="Update Purchase Order",
                timestamp=timestamp,
                related_objects=[
                    (po_id, "purchase_order", "primary"),
                    (supplier_id, "supplier", "reference"),
                ],
            )

            timestamp += timedelta(hours=random.randint(1, 8))

        add_event(
            events=events,
            relations=relations,
            event_id=next_event_id(),
            activity="Approve Purchase Order",
            timestamp=timestamp,
            related_objects=[
                (po_id, "purchase_order", "primary"),
                (cost_center_id, "cost_center", "reference"),
            ],
        )

        timestamp += timedelta(hours=random.randint(1, 6))

        add_event(
            events=events,
            relations=relations,
            event_id=next_event_id(),
            activity="Send Purchase Order",
            timestamp=timestamp,
            related_objects=[
                (po_id, "purchase_order", "primary"),
                (supplier_id, "supplier", "reference"),
            ],
        )

        delivery_batches = 2 if has_partial_delivery else 1

        for delivery_index in range(1, delivery_batches + 1):
            timestamp += timedelta(days=random.randint(1, 5))

            goods_receipt_id = f"{po_id}_gr_{delivery_index}"
            add_object(objects, goods_receipt_id, "goods_receipt", seen_objects)

            delivery_item_ids = (
                item_ids[: max(1, len(item_ids) // 2)]
                if has_partial_delivery and delivery_index == 1
                else item_ids
            )

            receive_goods_objects = [
                (po_id, "purchase_order", "reference"),
                (goods_receipt_id, "goods_receipt", "primary"),
            ]

            receive_goods_objects.extend(
                [(item_id, "item", "item") for item_id in delivery_item_ids]
            )

            add_event(
                events=events,
                relations=relations,
                event_id=next_event_id(),
                activity="Receive Goods",
                timestamp=timestamp,
                related_objects=receive_goods_objects,
            )

            timestamp += timedelta(hours=random.randint(1, 10))

            add_event(
                events=events,
                relations=relations,
                event_id=next_event_id(),
                activity="Record Goods Receipt",
                timestamp=timestamp,
                related_objects=[
                    (po_id, "purchase_order", "reference"),
                    (goods_receipt_id, "goods_receipt", "primary"),
                ],
            )

        for invoice_index in range(1, invoice_count + 1):
            timestamp += timedelta(days=random.randint(1, 7))

            invoice_id = f"{po_id}_inv_{invoice_index}"
            add_object(objects, invoice_id, "invoice", seen_objects)

            add_event(
                events=events,
                relations=relations,
                event_id=next_event_id(),
                activity="Receive Invoice",
                timestamp=timestamp,
                related_objects=[
                    (po_id, "purchase_order", "reference"),
                    (invoice_id, "invoice", "primary"),
                    (supplier_id, "supplier", "reference"),
                ],
            )

            timestamp += timedelta(hours=random.randint(2, 24))

            if has_slow_invoice_matching:
                timestamp += timedelta(days=random.randint(2, 10))

            add_event(
                events=events,
                relations=relations,
                event_id=next_event_id(),
                activity="Match Invoice",
                timestamp=timestamp,
                related_objects=[
                    (po_id, "purchase_order", "reference"),
                    (invoice_id, "invoice", "primary"),
                ],
            )

            if has_invoice_mismatch:
                timestamp += timedelta(hours=random.randint(4, 48))

                add_event(
                    events=events,
                    relations=relations,
                    event_id=next_event_id(),
                    activity="Resolve Invoice Mismatch",
                    timestamp=timestamp,
                    related_objects=[
                        (po_id, "purchase_order", "reference"),
                        (invoice_id, "invoice", "primary"),
                        (supplier_id, "supplier", "reference"),
                    ],
                )

                timestamp += timedelta(hours=random.randint(2, 24))

                add_event(
                    events=events,
                    relations=relations,
                    event_id=next_event_id(),
                    activity="Match Invoice",
                    timestamp=timestamp,
                    related_objects=[
                        (po_id, "purchase_order", "reference"),
                        (invoice_id, "invoice", "primary"),
                    ],
                )

            timestamp += timedelta(hours=random.randint(2, 24))

            add_event(
                events=events,
                relations=relations,
                event_id=next_event_id(),
                activity="Approve Invoice",
                timestamp=timestamp,
                related_objects=[
                    (po_id, "purchase_order", "reference"),
                    (invoice_id, "invoice", "primary"),
                ],
            )

            timestamp += timedelta(days=random.randint(1, 10))

            add_event(
                events=events,
                relations=relations,
                event_id=next_event_id(),
                activity="Pay Invoice",
                timestamp=timestamp,
                related_objects=[
                    (po_id, "purchase_order", "reference"),
                    (invoice_id, "invoice", "primary"),
                ],
            )

    events_df = pd.DataFrame(events)
    objects_df = pd.DataFrame(objects)
    relations_df = pd.DataFrame(relations)

    events_df[TIMESTAMP] = pd.to_datetime(events_df[TIMESTAMP])

    return OCEL(
        events=events_df,
        objects=objects_df,
        relations=relations_df,
    )


def save_p2p_ocel(
    base_path: str = "data/p2p_sample",
    purchase_order_count: int = 2000,
    seed: int = 42,
) -> None:
    """
    Save generated P2P OCEL tables as CSV files.

    The core app currently consumes:
    - events.csv
    - objects.csv
    - relations.csv

    Additional master-data-style CSV files are generated for future enrichment:
    - suppliers.csv
    - products.csv
    - cost_centers.csv
    """

    output_dir = Path(base_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    random.seed(seed)

    ocel = build_p2p_ocel(
        purchase_order_count=purchase_order_count,
        seed=seed,
    )

    master_data = build_master_data()

    ocel.events.to_csv(output_dir / "events.csv", index=False)
    ocel.objects.to_csv(output_dir / "objects.csv", index=False)
    ocel.relations.to_csv(output_dir / "relations.csv", index=False)

    master_data["suppliers"].to_csv(output_dir / "suppliers.csv", index=False)
    master_data["products"].to_csv(output_dir / "products.csv", index=False)
    master_data["cost_centers"].to_csv(output_dir / "cost_centers.csv", index=False)

    print("Synthetic P2P OCEL generated and saved.")
    print(f"Location: {output_dir}")
    print(f"Purchase orders: {purchase_order_count}")
    print(f"Events: {len(ocel.events)}")
    print(f"Objects: {len(ocel.objects)}")
    print(f"Relations: {len(ocel.relations)}")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a synthetic P2P object-centric event log."
    )

    parser.add_argument(
        "--output-dir",
        default="data/p2p_sample",
        help="Directory where generated CSV files will be saved.",
    )

    parser.add_argument(
        "--purchase-orders",
        type=int,
        default=2000,
        help="Number of purchase orders to generate.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible synthetic data.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    save_p2p_ocel(
        base_path=args.output_dir,
        purchase_order_count=args.purchase_orders,
        seed=args.seed,
    )