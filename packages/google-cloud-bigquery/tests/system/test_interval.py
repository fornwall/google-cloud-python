# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from dateutil.relativedelta import relativedelta

from google.cloud import bigquery


def test_interval_query_parameters(bigquery_client: bigquery.Client):
    value = relativedelta(years=-1, months=-2, days=3, microseconds=-1)
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("duration", "INTERVAL", value),
            bigquery.ScalarQueryParameter("empty", "INTERVAL", None),
            bigquery.ArrayQueryParameter("durations", "INTERVAL", [value, -value]),
            bigquery.StructQueryParameter(
                "record", bigquery.ScalarQueryParameter("duration", "INTERVAL", value)
            ),
        ]
    )

    rows = list(
        bigquery_client.query(
            "SELECT @duration, @empty, @durations, @record", job_config=job_config
        ).result()
    )

    assert len(rows) == 1
    assert tuple(rows[0]) == (value, None, [value, -value], {"duration": value})


def test_insert_rows_interval(bigquery_client: bigquery.Client, table_id: str):
    field = bigquery.SchemaField("duration", "INTERVAL")
    table = bigquery_client.create_table(
        bigquery.Table(
            table_id,
            schema=[
                bigquery.SchemaField("rowindex", "INTEGER"),
                field,
                bigquery.SchemaField("durations", "INTERVAL", mode="REPEATED"),
                bigquery.SchemaField("record", "RECORD", fields=[field]),
            ],
        )
    )
    value = relativedelta(years=1, months=2, days=-3, microseconds=-1)
    rows = [
        (0, value, [value, -value], {"duration": value}),
        (1, None, [], None),
    ]

    assert bigquery_client.insert_rows(table, rows) == []

    result = bigquery_client.query(
        f"SELECT * FROM `{table.full_table_id.replace(':', '.')}` ORDER BY rowindex"
    ).result()
    assert [tuple(row) for row in result] == rows
