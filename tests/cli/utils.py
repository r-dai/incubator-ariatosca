import logging


def setup_logger(logger_name,
                 output_stream,
                 logger_level=logging.INFO,
                 handlers=None,
                 remove_existing_handlers=True,
                 logger_format=None):
    """
    :param logger_name: Name of the logger.
    :param logger_level: Level for the logger (not for specific handler).
    :param handlers: An optional list of handlers (formatter will be
                     overridden); If None, only a StreamHandler for
                     sys.stdout will be used.
    :param remove_existing_handlers: Determines whether to remove existing
                                     handlers before adding new ones
    :param logger_format: the format this logger will have.
    :param propagate: propagate the message the parent logger.
    :return: A logger instance.
    :rtype: logging.Logger
    """
    logger = logging.getLogger(logger_name)

    if logger_format is None:
        # for easier parsing in tests, we prefer that the log will only include the message.
        logger_format = '%(message)s'

    formatter = logging.Formatter(fmt=logger_format)

    if remove_existing_handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)

    if not handlers:
        handler = logging.StreamHandler(output_stream)
        handler.setLevel(logging.DEBUG)
        handlers = [handler]

    for handler in handlers:
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(logger_level)
