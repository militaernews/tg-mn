drop table posts;

create table posts
(
    post_id        int not null,
    lang           char(2) not null,
    msg_id         int     not null,
    media_group_id varchar(120),
    reply_id       int,
    file_type      int,
    file_id        varchar(120),
    text           text,
    primary key (msg_id, lang)
);

-- Shared with ptb-suggest/ptb-mn (same DATABASE_URL). ptb-suggest's
-- /synthesize "Veröffentlichen" button writes rows here; scheduler.py reads
-- them and hands each off to Telegram's own native message scheduling.
-- Already created by ptb-suggest's/ptb-mn's own init_db() at startup - this
-- copy is just for reference, since tg-mn has no schema-migration step of
-- its own.
create table if not exists queued_posts
(
    id                    serial primary key,
    html                  text        not null,
    media                 text,
    created_at            timestamptz not null default now(),
    handed_off_at         timestamptz,
    scheduled_at          timestamptz,
    scheduled_message_id  int
);