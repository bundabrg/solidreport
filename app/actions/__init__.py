from . import send_staff_times_summary, send_staff_times_individual

ACTIONS = {
    a["name"]: a
    for a in (send_staff_times_summary.ACTION, send_staff_times_individual.ACTION)
}
