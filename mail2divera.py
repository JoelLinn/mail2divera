import os, email, time, requests, logging, json
from imapclient import IMAPClient
from email import policy
from datetime import datetime

DIVERA_URL = 'https://www.divera247.com/api/alarm?accesskey='

def parse_message(msg):
    # Leitstelle Olpe
    split = [w.strip() for w in msg.split(';')]
    info = {}
    info['gemeindeteil']            = split[1]
    info['strasse_hnr']             = split[2]
    info['objekt']                  = split[3]
    info['einsatzort_bemerkung']    = split[4]
    info['stichwort']               = split[5]
    info['diagnose']                = split[6]
    info['bemerkung']               = split[7]
    info['zugeteilt']               = split[8]
    return info

def build_alarm(info):
    alarm = ''
    alarm += info['stichwort'] + ','
    alarm += info['objekt'] + ','
    alarm += info['gemeindeteil'] + ','
    alarm += info['strasse_hnr'] + ','
    alarm += info['einsatzort_bemerkung'] + ','
    alarm += info['bemerkung'] + ','
    alarm += info['diagnose']
    return alarm

def trigger_divera(msg, DIVERA_ACCESSKEY):
    post = {'type':msg}
    r = requests.post(url=DIVERA_URL+DIVERA_ACCESSKEY, data=post).json()
    return r
        

def run(logger, IMAP_SERVER, IMAP_USER, IMAP_PASS, MAIL_FROM, MAIL_MAX_AGE, FETCH_INTERVAL, DIVERA_ACCESSKEY):

    M = IMAPClient(IMAP_SERVER)
    M.login(IMAP_USER, IMAP_PASS)
    M.select_folder(b'INBOX')

    while True:
        msgs = M.search([b'UNSEEN', b'FROM', MAIL_FROM])
        for msgId, data in M.fetch(msgs, [b'ENVELOPE', b'RFC822']).items():
            if (datetime.now() - data[b'ENVELOPE'].date).total_seconds() > MAIL_MAX_AGE:
                logger.warning('Message to old with mail id ' + str(msgId))
                continue
            msg = email.message_from_bytes(data[b'RFC822'], policy=policy.default)
            for part in (msg.iter_parts() if msg.is_multipart() else [msg]):
                if part.get_content_type() != 'text/plain':
                    continue
                parsed = parse_message(part.get_content())
                logger.info('Parsed content of mail id ' + str(msgId) + ': ' + json.dumps(parsed))
                alarm = build_alarm(parsed)
                if len(alarm) < 5:
                    logger.warning('Message to short with mail id ' + str(msgId) + ': "' + alarm + '"')
                    break
                logger.info('Triggering Divera with mail id ' + str(msgId) + ': "' + alarm + '"')
                result = trigger_divera(alarm[:30], DIVERA_ACCESSKEY)
                if result['success']:
                    logger.info('Success triggering Divera')
                else:
                    logger.warning('Failed triggering Divera : ' + result['message'])
                break
        time.sleep(FETCH_INTERVAL)
    M.logout()
    
if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s: %(message)s',
        level=logging.INFO
    )
    run(
        logging.getLogger(__name__),
        os.environ['IMAP_SERVER'],
        os.environ['IMAP_USER'],
        os.environ['IMAP_PASS'],
        os.environ['MAIL_FROM'],
        int(os.environ['MAIL_MAX_AGE']),
        int(os.environ['FETCH_INTERVAL']),
        os.environ['DIVERA_ACCESSKEY']
    )
