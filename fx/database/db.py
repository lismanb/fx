from contextlib import contextmanager

@contextmanager
def session_scope(is_autoflush=True):
    from sqlalchemy.orm import sessionmaker
    from fx.fxrates import db

    Session = db.scoped_session(sessionmaker(bind=db.engine))
    """Provide a transactional scope around a series of operations."""
    session = Session(autoflush=is_autoflush)
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        # Must be the Cap S session as remove isn't implmented on the instance
        Session.remove()



