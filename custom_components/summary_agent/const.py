"""Constants for Summary Agent."""

DOMAIN = "summary_agent"

CONF_AGENT_ID = "agent_id"


AREA_SUMMARY_SYSTEM_PROMPT = """
You are a Home Automation Agent for Home Assistant tasked with summarizing
the status of an area of the home. Your summaries are succinct, and do not
mention boring details or things that seem very mundane or minor. A
one sentence summary is best.

Here is an example of the input and output:

Area: Bedroom 1
- Bedroom 1 Light (Dimmable Smart Bulb)
    light: off
- Smart Lock (Encode Smart WiFi Deadbolt)
    binary_sensor: off
    binary_sensor Tamper: off
    binary_sensor Battery: off
    sensor Battery: 90 %
Summary: The bedroom is secure.

Area: Driveway
- Black Model 3 (Model 3)
  - binary_sensor Charging: off
  - sensor Battery level: 90%
  - sensor Battery range: 200 mi
- Gate Sensor
  - binary_sensor Pedestrian Gate: off
- Rainbird (TM2)
  - switch Sprinkler: off
Summary: The car is almost charged.
"""

AREA_SUMMARY_USER_PROMPT = """
Please summarize the following area:

Area: {{ area }}
{%- set devices = area_devices(area) -%}
{% for device in devices -%}
    {%- set iterated = true %}
    {%- if not device_attr(device, "disabled_by") and not device_attr(device, "entry_type") and device_attr(device, "name") %}
    {%- set device_name = device_attr(device, "name_by_user") | default(device_attr(device, "name"), True) %}
- {{ device_name  }}{% if device_attr(device, "model") and (device_attr(device, "model") | string) not in (device_attr(device, "name") | string) %} ({{ device_attr(device, "model") }}){% endif %}
    {%- set entity_info = namespace(printed=false) %}
    {%- for entity_id in device_entities(device) -%}
    {%- set entity_name = state_attr(entity_id, "friendly_name") | replace(device_name, "") | trim %}
  - {{ entity_id.split(".")[0] -}}
    {%- if entity_name %} {{ entity_name }}{% endif -%}
    : {{ states(entity_id, rounded=True, with_unit=True) }}
    {%- endfor %}
{%- endif %}
{%- endfor %}
{%- if not devices %}
- No devices
{%- endif %}
Summary:
"""


WEATHER_SUMMARY_SYSTEM_PROMPT = """
It is {{ now().strftime("%A %B %d %H:%M %p") }} in {{ location_text }}.

You are a Home Automation Agent for Home Assistant tasked with summarizing
the weather forecast. Your summaries are succinct and you do not mention
boring details that are mundane or minor, and don't elaborate too much
if the weather is the same as it has been.

Weather data will be provided in the following format:

Forecast:
Hourly weather forecast
- 10:00 AM: sunny (62°F 1% precip)
- 11:00 AM: sunny (63°F 1% precip)
- 12:00 PM: sunny (64°F 1% precip)
- 13:00 PM: sunny (65°F 1% precip)
Summary: It's going to be a pleasant day in with sunny skies and a high around 65 degrees Fahrenheit. Perfect for spending some time outdoors!


"It's going to be a beautiful sunny day today with a high of 78 degrees Fahrenheit. Perfect weather to spend some time outdoors!"



"""

WEATHER_SUMMARY_USER_PROMPT = """
It is {{ now().strftime("%A %B %d %H:%M %p") }} in {{ location_text }}.

Current Time: {{ now().strftime("%A %B %d %H:%M %p") }}
Hourly weather forecast:
{%- set temperature_unit = state_attr(weather_entity, 'temperature_unit') -%}
{% for forecast in forecast_response.forecast -%}
- {{ forecast.datetime.strftime("%H:%M %p") }}: {{ forecast.condition }} ({{ forecast.temperature }}{{ temperature_unit }}, {{ forecast.precipitation }}% precip)
{%- endif %}
"""
