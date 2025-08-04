"""
Create a report for a client that shows the work done by all members, broken down by date and summarised by
project
"""

import datetime
import tempfile
from math import ceil, floor
from pathlib import Path
from typing import Dict

import click
from gotenberg_client.options import PageMarginsType, Measurement, MeasurementUnitType
from psycopg2 import Error
from psycopg2.extras import NamedTupleCursor

import systems
from .models import (
    DataModel,
    MemberDataModel,
    DateDataModel,
    DateSummaryModel,
    ClientDataModel,
    ProjectDataModel,
    TimeEntryDataModel,
    ProjectSummaryModel,
)


@click.command("staff_times")
@click.option("--output", help="Output file (Default: output.pdf)")
@click.option("--organization-id", help="Organization UUID (Required)")
@click.option("--template", help="Which Template to use (Default:staff_times")
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
@click.option("--member-id-filter", help="Filter by member id")
@click.option("--project-filter", help="Filter by project (partial match)")
@click.option("--member-filter", help="Filter by member (partial match)")
@click.option("--client-filter", help="Filter by Client Name (partial match)")
@click.option(
    "--resource",
    help="Add a resource readable by the template ([name:]file)",
    multiple=True,
)
@click.option(
    "--debug", help="Write the html file out as well", default=False, is_flag=True
)
@click.pass_context
def generate(
    ctx,
    output,
    organization_id,
    template,
    footer_template,
    start,
    end,
    project_filter,
    member_filter,
    member_id_filter,
    client_filter,
    resource,
    debug,
):
    cfg = ctx.obj["config"]
    db = systems.database(cfg)
    env = systems.jinja(cfg)
    gotenberg = systems.gotenberg(cfg)

    # Apply defaults
    args = {
        "output": output,
        "organization_id": organization_id,
        "template": template,
        "footer_template": footer_template,
        "start": start.date() if start is not None else None,
        "end": end.date() if end is not None else None,
        "project_filter": project_filter,
        "member_filter": member_filter,
        "client_filter": client_filter,
        "member_id_filter": member_id_filter,
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

    # Add resources if any passed
    resource = cfg.defaults.get("resource", []) + list(resource)

    args["resources"] = {}
    for r in resource:
        r_split = r.split(":", 1)
        r_path = r_split[1] if len(r_split) == 2 else r
        args["resources"][r_split[0]] = cfg.sr_data.joinpath(r_path)

    # Map output under sr-data
    args["output"] = str(cfg.sr_data.joinpath(args["output"]))

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
    output="output.pdf",
    organization_id=None,
    project_filter="",
    member_filter="",
    member_id_filter=None,
    client_filter="",
    start=datetime.date.today(),
    end=datetime.date.today(),
    footer_template="footer",
    template="staff_times",
    resources: Dict[str, Path] = None,
    debug=False,
):
    resources = resources or {}
    try:
        with db.cursor(cursor_factory=NamedTupleCursor) as cursor:
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
                    { "AND clients.name ilike %(client)s" if client_filter else "" }
                    { "AND projects.name ilike %(project)s" if project_filter else "" }
                    { "AND users.name ilike %(member)s" if member_filter else "" }
                    { "AND users.id = %(member_id)s" if member_id_filter else "" }
                  """

            cursor.execute(
                sql,
                {
                    "organization_id": organization_id,
                    "start": start.isoformat(),
                    "end": (end + datetime.timedelta(days=1)).isoformat(),
                    "project": "%{}%".format(project_filter),
                    "member": "%{}%".format(member_filter),
                    "client": "%{}%".format(client_filter),
                    "member_id": member_id_filter,
                },
            )
            records = cursor.fetchall()

    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
        return
    finally:
        cursor.close()

    # Parse out time entries
    data = DataModel(start=start, end=end)
    for r in records:
        if r.user_id not in data.members:
            data.members[r.user_id] = MemberDataModel(name=r.user_name)
        member_data = data.members[r.user_id]

        start_date = r.start.date()

        if start_date not in member_data.dates:
            member_data.dates[start_date] = DateDataModel(date=start_date)
        if start_date not in data.summary.dates:
            data.summary.dates[start_date] = DateSummaryModel(date=start_date)
        date_data = member_data.dates[start_date]

        if r.client_id not in date_data.clients:
            date_data.clients[r.client_id] = ClientDataModel(
                name=r.client_name or "(No Client)"
            )
        client_data = date_data.clients[r.client_id]

        if r.project_id not in client_data.projects:
            client_data.projects[r.project_id] = ProjectDataModel(
                name=r.project_name or "(No Project)"
            )
        project_data = client_data.projects[r.project_id]

        if r.project_id not in data.summary.projects:
            data.summary.projects[r.project_id] = ProjectSummaryModel(
                name=r.project_name or "(No Project)",
                client_name=r.client_name or "(No Client)",
            )

        duration = int((r.end - r.start).total_seconds())

        project_data.time_entries.append(
            TimeEntryDataModel(
                start_time=r.start,
                end_time=r.end,
                duration=duration,
                description=r.description,
            )
        )

        # Add Non duplicated descriptions
        if r.description not in project_data.descriptions:
            project_data.descriptions.append(r.description)

        project_data.duration += duration
        client_data.duration += duration
        date_data.duration += duration
        member_data.duration += duration
        data.duration += duration
        data.summary.projects[r.project_id].duration += duration

    # Perform rounding. Time over a day per member is rounded up to the nearest 30 minutes unless within 15% (4.5 minutes) of
    # lower boundary in which case it rounds down unless it would round to 0.
    data.duration = 0
    for _, member_data in data.members.items():
        member_data.duration = 0
        for date, date_data in member_data.dates.items():
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

            date_data.duration = duration
            data.summary.dates[date].duration += duration
            member_data.duration += duration
            data.duration += duration

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
