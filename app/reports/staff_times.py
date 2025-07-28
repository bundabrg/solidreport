import datetime
import tempfile
from math import ceil, floor
from pathlib import Path

import click
from gotenberg_client.options import PageMarginsType, Measurement, MeasurementUnitType
from psycopg2 import Error
from psycopg2.extras import NamedTupleCursor

import systems


@click.command("staff_times")
@click.argument("output", default="output.pdf")
@click.option("--organization", help="Organization UUID")
@click.option("--template", help="Which Template to use (Default:staff_times")
@click.option(
    "--footer-template",
    help="Which template to use for the footer (Default:footer)",
)
@click.option(
    "--start",
    help="Start Date (YYYY-MM-DD) (Default:today)",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=str(datetime.date.today())
)
@click.option(
    "--end",
    help="End Date (YYYY-MM-DD) (Default:today)",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=str(datetime.date.today())
)
@click.option("--project", help="Filter by project (partial match)")
@click.option("--member", help="Filter by member (partial match)")
@click.option("--client", help="Filter by client (partial match)")
@click.option(
    "--add",
    help="Add a file as a resource. Can be called multiple times",
    multiple=True,
)
@click.pass_context
def generate(
    ctx,
    **args,
):
    output = args.get("output")
    start = args.get("start")
    end = args.get("end")

    print(f"Generating {output} from {start.date()} to {end.date()}")
    cfg = ctx.obj["config"]
    db = systems.database(cfg)
    env = systems.jinja(cfg)
    gotenberg = systems.gotenberg(cfg)

    # Apply defaults and remove any values set to None
    args = {
        k: v
        for k, v in {
            k: v if v is not None else cfg.defaults.get(k) for k, v in args.items()
        }.items()
        if v is not None
    }

    if args.get("organization") is None:
        args["organization"] = str(cfg.defaults.organization)
    if args.get("organization") is None:
        raise Exception("No organization specified")

    report(db, env, gotenberg, **args)


def report(
    db,
    env,
    gotenberg,
    output="output.pdf",
    organization=None,
    add=None,
    project="",
    member="",
    client="",
    start=datetime.date.today(),
    end=datetime.date.today(),
    footer_template="footer",
    template="staff_times",
):
    add = add if add is not None else []
    try:
        with db.cursor(cursor_factory=NamedTupleCursor) as cursor:
            sql = """
                SELECT te.start, te.end, te.description, users.name as user_name,
                     clients.name as client_name, projects.name as project_name
                FROM users JOIN members ON (members.user_id = users.id)
                     JOIN time_entries te ON (te.member_id = members.id)
                     LEFT JOIN projects ON (te.project_id = projects.id)
                     LEFT JOIN clients ON (projects.client_id = clients.id)
                WHERE te.organization_id = %(organization_id)s
                    AND te.start >= %(start)s
                    AND te.end < %(end)s
                    AND (clients.name is null or clients.name ilike %(client)s)
                    AND (projects.name is null or projects.name ilike %(project)s)
                    AND users.name ilike %(member)s
                  """

            cursor.execute(
                sql,
                {
                    "organization_id": organization,
                    "start": start.isoformat(),
                    "end": (end + datetime.timedelta(days=1)).isoformat(),
                    "project": "%{}%".format(project),
                    "member": "%{}%".format(member),
                    "client": "%{}%".format(client),
                },
            )
            records = cursor.fetchall()

    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
        return
    finally:
        cursor.close()

    # Parse out time entries
    members = {}
    for r in records:
        member_name = r.user_name
        if member_name not in members:
            members[member_name] = {
                "total_duration": 0,
                "dates": {},
            }

        start_date = r.start.date()

        if start_date not in members[member_name]["dates"]:
            members[member_name]["dates"][start_date] = {
                "clients": {},
            }

        if r.client_name not in members[member_name]["dates"][start_date]["clients"]:
            members[member_name]["dates"][start_date]["clients"][r.client_name] = {
                "projects": {},
            }

        if (
            r.project_name
            not in members[member_name]["dates"][start_date]["clients"][r.client_name][
                "projects"
            ]
        ):
            members[member_name]["dates"][start_date]["clients"][r.client_name][
                "projects"
            ][r.project_name] = {
                "duration": 0,
                "description": [],
            }
        if len(r.description):
            members[member_name]["dates"][start_date]["clients"][r.client_name][
                "projects"
            ][r.project_name]["description"].append(r.description)

        duration = (r.end - r.start).seconds
        members[member_name]["dates"][start_date]["clients"][r.client_name]["projects"][
            r.project_name
        ]["duration"] += duration

    dates = {}

    # Perform rounding. Time for the member is rounded up to the nearest 30 minutes based on the duration during the day
    # unless its within 15% of 30 minutes (4.5 minutes) of a boundary in which case it rounds down unless it would
    # round to 0 in which case it rounds up.
    global_duration = 0
    for _, member in members.items():
        total_duration = 0
        for date_name, date in member["dates"].items():
            if date_name not in dates:
                dates[date_name] = {
                    "total_duration": 0,
                }

            date_duration = 0
            for _, client in date["clients"].items():
                for _, project in client["projects"].items():
                    date_duration += project["duration"]

            half_hours = date_duration / 60 / 30
            delta = half_hours - floor(half_hours)
            if delta < 0.15 and half_hours > 1:
                duration_rounded = floor(half_hours) * 30 * 60
            else:
                duration_rounded = ceil(half_hours) * 30 * 60
            date["duration"] = duration_rounded
            total_duration += duration_rounded

            dates[date_name]["total_duration"] = duration_rounded

        member["total_duration"] = total_duration
        global_duration += total_duration

    # Put it in a format the template expects
    data = {
        "config": {
            "start": start,
            "end": end,
        },
        "summary": {
            "total_duration": global_duration,
            "dates": sorted(
                [
                    {
                        "date": date_name,
                        "duration": date["total_duration"],
                    }
                    for date_name, date in dates.items()
                ],
                key=lambda x: x["date"],
            ),
            "members": sorted(
                [
                    {
                        "name": member_name,
                        "duration": member["total_duration"],
                    }
                    for member_name, member in members.items()
                ],
                key=lambda x: x["name"],
            ),
        },
        "members": sorted(
            [
                {
                    "name": member_name,
                    "duration": member["total_duration"],
                    "dates": sorted(
                        [
                            {
                                "date": date_name,
                                "duration": date["duration"],
                                "clients": sorted(
                                    [
                                        {
                                            "name": client_name,
                                            "projects": sorted(
                                                [
                                                    {
                                                        "name": project_name,
                                                        "duration": project["duration"],
                                                        "description": project[
                                                            "description"
                                                        ],
                                                    }
                                                    for project_name, project in client[
                                                        "projects"
                                                    ].items()
                                                ],
                                                key=lambda x: x["name"],
                                            ),
                                        }
                                        for client_name, client in date[
                                            "clients"
                                        ].items()
                                    ],
                                    key=lambda x: x["name"],
                                ),
                            }
                            for date_name, date in member["dates"].items()
                        ],
                        key=lambda x: x["date"],
                    ),
                }
                for member_name, member in members.items()
            ],
            key=lambda x: x["name"],
        ),
    }

    tmpl = env.get_template(template + ".html")
    with tempfile.NamedTemporaryFile() as tmp:
        tmpl_footer = env.get_template(footer_template + ".html")
        tmp.write(tmpl_footer.render(data=data, add=add).encode("utf-8"))
        tmp.flush()

        with gotenberg() as client:
            with client.chromium.html_to_pdf() as route:
                response = (
                    route.string_index(tmpl.render(data=data, add=add))
                    .margins(
                        PageMarginsType(
                            bottom=Measurement(100, MeasurementUnitType.Pixels)
                        )
                    )
                    .resources([Path(a) for a in add])
                    .footer(Path(tmp.name))
                    .run()
                )
                response.to_file(Path(output))

    return data
