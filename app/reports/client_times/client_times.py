"""
Create a report for a client that shows the work done by all members, broken down by date and summarised by
project
"""

import datetime
import sys
import tempfile
from math import ceil, floor
from pathlib import Path
from typing import Dict
from uuid import UUID

import click
from gotenberg_client.options import PageMarginsType, Measurement, MeasurementUnitType
from psycopg2 import Error
from psycopg2.extras import NamedTupleCursor

import systems
from .models import (
    DataModel,
    ProjectDataModel,
    DateDataModel,
    MemberDataModel,
    TimeEntryDataModel,
    ClientDataModel,
    DateSummaryModel,
)


def find_client(db, search: str) -> UUID | None:
    """
    Lookup Client ID against its name
    :param db: Database
    :param search: Search string
    :return: Client ID
    """
    with db.cursor(cursor_factory=NamedTupleCursor) as cursor:
        sql = f"""
            SELECT clients.id as client_id
            FROM clients
            WHERE clients.name ilike %(search)s
        """

        cursor.execute(
            sql,
            {
                "search": "%{}%".format(search),
            },
        )

        result = cursor.fetchone()
        return result.client_id if result is not None else None


@click.command("client_times")
@click.option("--output", help="Output file (Default: output.pdf)")
@click.option("--client-id", help="Filter by Client ID (Default: (No Client))")
@click.option("--client-filter", help="Filter by Client Name (Default: (No Client))")
@click.option("--organization-id", help="Organization UUID (Required)")
@click.option("--template", help="Which Template to use (Default:client_times")
@click.option(
    "--footer-template",
    help="Which template to use for the footer (Default:footer)",
)
@click.option(
    "--start",
    help="Start Date (YYYY-MM-DD) (Default:today)",
    type=click.DateTime(formats=["%Y-%m-%d"]),
)
@click.option(
    "--end",
    help="End Date (YYYY-MM-DD) (Default:today)",
    type=click.DateTime(formats=["%Y-%m-%d"]),
)
@click.option("--project-filter", help="Filter by project (partial match)")
@click.option("--member-filter", help="Filter by member (partial match)")
@click.option(
    "--resource", help="Add a resource readable by the template ([name:]file)", multiple=True
)
@click.option(
    "--debug", help="Write the html file out as well", default=False, is_flag=True
)
@click.pass_context
def generate(
    ctx,
    client_id,
    client_filter,
    output,
    organization_id,
    template,
    footer_template,
    start,
    end,
    project_filter,
    member_filter,
    resource,
    debug,
):
    cfg = ctx.obj["config"]
    db = systems.database(cfg)
    env = systems.jinja(cfg)
    gotenberg = systems.gotenberg(cfg)

    # Apply defaults
    args = {
        "client_id": client_id,
        "output": output,
        "organization_id": organization_id,
        "template": template,
        "footer_template": footer_template,
        "start": start.date() if start is not None else None,
        "end": end.date() if end is not None else None,
        "project_filter": project_filter,
        "member_filter": member_filter,
    }
    defaults = {
        "start": datetime.date.today(),
        "end": datetime.date.today(),
        "output": "output.pdf",
    }
    args = {
        k: v if v is not None else cfg.defaults.get(k, defaults.get(k))
        for k, v in args.items()
    }

    # Sanity Checks
    if args.get("organization_id") is None:
        raise Exception("No organization_id specified")

    # If no client_id and client_filter is specified try to resolve to an id
    if args["client_id"] is None and client_filter is not None:
        args["client_id"] = find_client(db, client_filter)

    # Add resources if any passed
    resource = cfg.defaults.get("resource", []) + list(resource)

    args["resources"] = {}
    for r in resource:
        r_split = r.split(":", 1)
        r_path = r_split[1] if len(r_split) == 2 else r
        args["resources"][r_split[0]] = cfg.sr_data.joinpath(r_path)

    # Map output under sr-data
    args['output'] = str(cfg.sr_data.joinpath(args['output']))

    print(f"Generating {args['output']} from {args['start']} to {args['end']}")

    report(
        db,
        env,
        gotenberg,
        debug=debug,
        **{k: v for k, v in args.items() if v is not None},
    )


def report(
    db,
    env,
    gotenberg,
    client_id=None,
    output="output.pdf",
    organization_id=None,
    project_filter="",
    member_filter="",
    start=datetime.date.today(),
    end=datetime.date.today(),
    footer_template="footer",
    template="client_times",
    resources: Dict[str, Path] = None,
    debug=False,
):
    resources = resources or {}
    try:
        with db.cursor(cursor_factory=NamedTupleCursor) as cursor:
            sql = f"""
                SELECT clients.id as client_id, clients.name as client_name
                FROM clients
                WHERE { "clients.id = %(client_id)s" if client_id else "clients.id is null" }
            """

            cursor.execute(
                sql,
                {
                    "client_id": client_id,
                },
            )

            records = cursor.fetchone()
            client_name = records.client_name if records else "(No Client)"

            sql = f"""
                SELECT te.start, te.end, te.description, users.id as user_id, users.name as user_name,
                     clients.id as client_id, clients.name as client_name, 
                     projects.id as project_id, projects.name as project_name, projects.billable_rate as project_billable_rate,
                     te.billable_rate, te.billable, organizations.billable_rate as organization_billable_rate
                FROM users JOIN members ON (members.user_id = users.id)
                     JOIN time_entries te ON (te.member_id = members.id)
                     LEFT JOIN projects ON (te.project_id = projects.id)
                     LEFT JOIN clients ON (te.client_id = clients.id)
                     JOIN organizations ON (te.organization_id = organizations.id)
                WHERE te.organization_id = %(organization_id)s
                    AND te.start >= %(start)s
                    AND te.end < %(end)s
                    { "AND clients.id = %(client)s" if client_id else "AND clients.id is null" }
                    { "AND projects.name ilike %(project)s" if project_filter else "" }
                    { "AND users.name ilike %(member)s" if member_filter else "" }
                  """

            cursor.execute(
                sql,
                {
                    "organization_id": organization_id,
                    "start": start.isoformat(),
                    "end": (end + datetime.timedelta(days=1)).isoformat(),
                    "project": "%{}%".format(project_filter),
                    "member": "%{}%".format(member_filter),
                    "client": client_id,
                },
            )
            records = cursor.fetchall()

    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
        return
    finally:
        cursor.close()

    # Parse out time entries
    data = DataModel(
        client=ClientDataModel(id=client_id, name=client_name), start=start, end=end
    )
    for r in records:
        project_id = r.project_id
        if project_id not in data.projects:
            data.projects[project_id] = ProjectDataModel(
                name=r.project_name if r.project_name is not None else "(No Project)",
                billable_rate=(
                    r.project_billable_rate
                    if r.project_billable_rate is not None
                    else r.organization_billable_rate
                ),
            )
        project_data = data.projects[project_id]

        start_date = r.start.date()

        if start_date not in project_data.dates:
            project_data.dates[start_date] = DateDataModel(date=start_date)
        if start_date not in data.summary.dates:
            data.summary.dates[start_date] = DateSummaryModel(date=start_date)
        date_data = project_data.dates[start_date]

        if r.user_id not in date_data.members:
            date_data.members[r.user_id] = MemberDataModel(name=r.user_name)
        member_data = date_data.members[r.user_id]

        duration = int((r.end - r.start).total_seconds())

        member_data.time_entries.append(
            TimeEntryDataModel(
                start_time=r.start,
                end_time=r.end,
                duration=duration,
                description=r.description,
            )
        )

        member_data.duration += duration
        date_data.duration += duration
        project_data.duration += duration
        data.duration += duration

    # Perform rounding. Time over a day per project is rounded up to the nearest 30 minutes unless within 15% (4.5 minutes) of
    # lower boundary in which case it rounds down unless it would round to 0.
    data.duration = 0
    for _, project_data in data.projects.items():
        project_data.duration = 0
        for date, date_data in project_data.dates.items():
            half_hours = date_data.duration / 60 / 30
            delta = half_hours - floor(half_hours)
            duration = (
                (
                    floor(half_hours)
                    if delta < 0.15 and half_hours > 1
                    else ceil(half_hours)
                )
                * 30
                * 60
            )
            cost = project_data.billable_rate * (duration / 60 / 60)

            date_data.duration = duration
            date_data.cost = cost
            data.summary.dates[date].duration += duration
            project_data.duration += duration
            project_data.cost += cost
            data.duration += duration
            data.cost += cost

    resources_available = [k for k, _ in resources.items()]
    tmpl = env.get_template(template + ".html")
    if debug:
        with open("{}-debug.html".format(output), "w") as f:
            f.write(tmpl.render(data=data, resources=resources_available))
    with tempfile.NamedTemporaryFile() as tmp:
        tmpl_footer = env.get_template(footer_template + ".html")
        tmp.write(
            tmpl_footer.render(data=data, resources=resources_available).encode("utf-8")
        )
        tmp.flush()

        with gotenberg() as client:
            with client.chromium.html_to_pdf() as route:
                builder = (
                    route.string_index(
                        tmpl.render(data=data, resources=resources_available)
                    )
                    .margins(
                        PageMarginsType(
                            bottom=Measurement(100, MeasurementUnitType.Pixels)
                        )
                    )
                    .footer(Path(tmp.name))
                )

                for name, path in resources.items():
                    builder.resource(path, name=name)

                response = builder.run()
                response.to_file(Path(output))

    return data
