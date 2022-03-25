import logging

import ldap

from trigram.helpers.app_logger import AppLogger
from trigram.webapp.config import Config

logging.setLoggerClass(AppLogger)

config = Config()

logger = logging.getLogger(__name__)


def fetch_ldap_cn_list():
    logger.info("Establishing connection...")

    try:
        ldap_conn = ldap.initialize(config.LDAP_CON_URL)
        logger.info("Connection to server succeeded...")
    except ldap.SERVER_DOWN:
        raise

    # Set LDAP protocol version used
    ldap_conn.protocol_version = ldap.VERSION3

    if config.LDAP_CACERTFILE is not None:
        # Force cert validation
        ldap_conn.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_DEMAND)
        # Set path name of file containing all trusted CA certificates
        ldap_conn.set_option(ldap.OPT_X_TLS_CACERTFILE, config.LDAP_CACERTFILE)
        # Force libldap to create a new SSL context (must be last TLS option!)
        ldap_conn.set_option(ldap.OPT_X_TLS_NEWCTX, 0)

    try:
        ldap_conn.simple_bind_s(config.LDAP_BIND_USER, config.LDAP_BIND_PASSWORD)
        logger.info("Simple bind successful...")
    except ldap.INVALID_CREDENTIALS:
        raise

    logger.info("Connection to LDAP server successful!!!")

    try:
        ldap_result_list = ldap_conn.search_s(
            config.LDAP_USERS_DN,
            ldap.SCOPE_SUBTREE,
            filterstr="(!(cn=users))",
            attrlist=["cn"],
        )
    except ldap.LDAPError as err:
        ldap_result_list = None
        logger.error(err)

    logger.info("Disconnecting...")
    ldap_conn.unbind_s()
    logger.info("Done!")

    if ldap_result_list is not None:
        return sorted([x[1]["cn"][0].decode("utf-8") for x in ldap_result_list])
    return False
