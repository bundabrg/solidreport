from . import send_staff_times_summary, send_staff_times_individual, send_client_times

ACTIONS = {
    a["name"]: a
    for a in (
        send_staff_times_summary.ACTION,
        send_staff_times_individual.ACTION,
        send_client_times.ACTION,
    )
}
