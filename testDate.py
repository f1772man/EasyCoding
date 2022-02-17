from datetime import datetime
 
now = datetime.now()
ampm = now.strftime('%p')
ampm_kr = '오전' if ampm == 'AM' else '오후'
print(ampm_kr)