analyze_prompt = """
You are an assistant to the users and you are having a conversation with them. \
Your goal is to understand and extract the topic of the guide the user needs.

"""

input_prompt = """
You are an assistant to the users and you are having a conversation with them. \
Your goal is to assist the user and get necessary information from the input.

You should ask him if the necessary information is not mentioned

necessary info:

"""

guides_prompt = """
You are an assistant for helping to perform a process and you are having a conversation with the user. 

### Here is the step-by-step guide of the process:

{}

### 

You should go through the guide step by step with the user, explaining at each step what he should do. \
You should also answer his questions about the guide, help solve problems if they arise during the process.

#### Instructions:
1. Make sure that your responses are providing information step by step, one step per response.
2. Always ask for user feedback after each step.
3. Directly jump to the guide, no need for greeting.
"""

switch_prompt = """
You are an assistant to the user. The user has an issue, here is his query {}.
The user is answering to the question: "Do you want to fix the issue right now or would like to finish the installation guide first?"

You must understand from the user response whether he wants to fix it now, or would like to continue the installation guide.
"""

issues_prompt = """
You are an assistant for users. Your goal is to help users resolve the given issue.

### Here is the troubleshooting guide for it:

{}.

###

#### Instructions:
1. Make sure that your responses are providing information step by step, one step per response.
2. Always ask for user feedback after each step.
"""

dot1x_guide = """
Install Dot1x for Windows 10
    1. From the desktop, right-click on the wireless icon on the bottom right corner of your desktop. Select Open Network and Sharing Center.
    2. In the Network and Sharing Center, select Setup a new connection or network. In description, "Set up a broadband, dial-up, or VPN connection, or set up a router or access point".
    3. Select Manually connect to a new network. Connect to hidden network or create a new wireless
    profile.
    4. Enter the information for new connection (SSID): Manually connect to a wireless network, select the Network name, Security Type (WPA2-Enterprise from dropdown list), Encryption
    Type (AES), Security Key(empty), Hide characters(unchecked), Start this connection automatically(checked), Connect even if the
    network is not broadcasting(unchecked).
    5. Click the Change connection settings box.
    6. Click on the Security Tab on the top of the window.
    7. Select network authentication method. In our example is it EAP (PEAP). Remember my credentials
    should be checked.
    8. Under Advanced settings (at the bottom) you could select Authentication mode:
    Check the Specify authentication mode from 802.1X settings Tab.
    9. After connection you will be prompted for Username and password that will be used for Dot1x
    authentication
"""

dns_issue = """
DNS Troubleshooting
DNS Troubleshooting using Nile Portal					
Let's say If a customer reported saying that DNS server is not reachable. We need to first identify whether DNS is not \
reachable for the end host device or its not reachable from the NSB elements
To check if the DNS is reachable or not from Infrastructure (Nile Service blocks)					
1.Check the Nile Portal (NP) Dashboard → Infrastructure → DNS Tile				
If Green: DNS server(s) have passed NSB reachability → proceed further to check Devices DNS Tile
If Red: DNS server(s) are failing NSB reachability → Global DNS issue
2. Click on the DNS tile and check the availability status and Experience

The window has columns "Status", "Name", "Type", "IP Address", "Availability", "Experience" and below is a "Floor" \
table with columns "Floor Name", "AQI", "Internet", "DNS ”, “DHCP”, “RADIUS”. See the DNS column in the Floors table.

a)Click on 8.8.8.8 / 192.168.1.9 (Customers internal DNS server) and check the performance graph for any error or drops.
b)Check the DNS section under floors Column - A Blue Tick indicates that the reachability to DNS is fine

Steps:

a)Hover the cursor on the graph and check for the Availability -> It should be true.
b)if the availability is false for a specific day or time it means that there was an outage detected.

See performance and availability graphics.

3. Check the Nile Portal (NP) Devices page → Problem type → DNS tile:			
• If Red:
• Click on the DNS tile to display the affected clients

Click on an affected client to troubleshoot a ‘Client specific DNS issue’. • If Green: Problem is likely a client \
issue and not a Nile issue.
How I could add new DNS server IP address from Nile Portal?					
From Infrastructure Tile on Nile Dashboard, you could see DNS servers IP addresses used during provisioning as well \
as the one used for Clients.
For client DNS Server change, it should be changed from DHCP Server side. Nile will snoop that new DNS server. No \
changes of DNS server are needed from Nile Portal.

"""

issue_example = """
Troubleshooting Guide: No Internet Connection

Problem: You are unable to connect to the internet.

Possible Causes:

Network Hardware Issues: Your modem, router, or cables may be faulty or improperly connected.
Service Provider Outage: Your internet service provider (ISP) may be experiencing an outage.
Device Configuration: Your computer or device may have network configuration issues.
Wireless Connectivity Issues: If using Wi-Fi, there could be interference or signal problems.
Software or Malware: Software or malware issues on your computer can disrupt internet connectivity.
Troubleshooting Steps:

1. Check Hardware:

Ensure all cables (power, Ethernet, coaxial) are securely connected.
Power cycle your modem and router (unplug, wait 30 seconds, then plug back in).
Verify that the lights on your modem and router are as expected (consult device documentation).
2. Check for ISP Outage:

Visit your ISP's website or contact their customer support to check for service outages in your area.
3. Reboot Your Computer/Device:

Restart your computer or device to refresh network settings.
4. Check Network Settings:

Confirm that your device's network settings are correctly configured.
Ensure your device is set to obtain an IP address automatically (DHCP).
5. Wi-Fi Troubleshooting (if using Wi-Fi):

Move closer to the router to improve signal strength.
Try connecting to a different Wi-Fi network if available.
Reboot your router.
6. Check for Software Issues:

Disable any third-party firewalls or security software temporarily.
Run a malware scan with an updated antivirus program.
7. Contact Your ISP:

If none of the above steps resolve the issue, contact your ISP's customer support for further assistance.
Remember to document any changes you make during troubleshooting, and be cautious when altering settings on your devices or network equipment. If the problem persists, it's advisable to seek professional assistance.
"""
