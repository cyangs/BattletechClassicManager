--
-- PostgreSQL database dump
--

\restrict RkmxuBXOXXzjwiLkacgldlGQpzj9Ztj731RVpTqCHdyR1Fh5dTp9i4yxzSUNfUM

-- Dumped from database version 17.11
-- Dumped by pg_dump version 17.11 (Debian 17.11-1.pgdg13+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE IF EXISTS ONLY public.weapon_attachment_link DROP CONSTRAINT IF EXISTS weapon_attachment_link_weapon_id_fkey;
ALTER TABLE IF EXISTS ONLY public.weapon_attachment_link DROP CONSTRAINT IF EXISTS weapon_attachment_link_attachment_sku_fkey;
ALTER TABLE IF EXISTS ONLY public.weapon_ammo_link DROP CONSTRAINT IF EXISTS weapon_ammo_link_weapon_id_fkey;
ALTER TABLE IF EXISTS ONLY public.weapon_ammo_link DROP CONSTRAINT IF EXISTS weapon_ammo_link_ammo_sku_fkey;
ALTER TABLE IF EXISTS ONLY public.session_weapon_states DROP CONSTRAINT IF EXISTS session_weapon_states_session_mech_id_fkey;
ALTER TABLE IF EXISTS ONLY public.session_mechs DROP CONSTRAINT IF EXISTS session_mechs_session_id_fkey;
ALTER TABLE IF EXISTS ONLY public.session_mechs DROP CONSTRAINT IF EXISTS session_mechs_mech_id_fkey;
ALTER TABLE IF EXISTS ONLY public.session_mech_weapons DROP CONSTRAINT IF EXISTS session_mech_weapons_weapon_id_fkey;
ALTER TABLE IF EXISTS ONLY public.session_mech_weapons DROP CONSTRAINT IF EXISTS session_mech_weapons_session_mech_id_fkey;
ALTER TABLE IF EXISTS ONLY public.session_mech_attachments DROP CONSTRAINT IF EXISTS session_mech_attachments_session_mech_id_fkey;
ALTER TABLE IF EXISTS ONLY public.session_mech_attachments DROP CONSTRAINT IF EXISTS session_mech_attachments_attachment_sku_fkey;
ALTER TABLE IF EXISTS ONLY public.session_events DROP CONSTRAINT IF EXISTS session_events_session_mech_id_fkey;
ALTER TABLE IF EXISTS ONLY public.session_events DROP CONSTRAINT IF EXISTS session_events_session_id_fkey;
ALTER TABLE IF EXISTS ONLY public.mech_weapons DROP CONSTRAINT IF EXISTS mech_weapons_weapon_id_fkey;
ALTER TABLE IF EXISTS ONLY public.mech_weapons DROP CONSTRAINT IF EXISTS mech_weapons_mech_id_fkey;
ALTER TABLE IF EXISTS ONLY public.mech_attachment_link DROP CONSTRAINT IF EXISTS mech_attachment_link_mech_id_fkey;
ALTER TABLE IF EXISTS ONLY public.mech_attachment_link DROP CONSTRAINT IF EXISTS mech_attachment_link_attachment_sku_fkey;
DROP INDEX IF EXISTS public.ix_session_events_session_id;
ALTER TABLE IF EXISTS ONLY public.weapons_master DROP CONSTRAINT IF EXISTS weapons_master_pkey;
ALTER TABLE IF EXISTS ONLY public.weapons_master DROP CONSTRAINT IF EXISTS weapons_master_name_key;
ALTER TABLE IF EXISTS ONLY public.attachments DROP CONSTRAINT IF EXISTS weapon_attachments_pkey;
ALTER TABLE IF EXISTS ONLY public.weapon_attachment_link DROP CONSTRAINT IF EXISTS weapon_attachment_link_pkey;
ALTER TABLE IF EXISTS ONLY public.weapon_ammo_link DROP CONSTRAINT IF EXISTS weapon_ammo_link_pkey;
ALTER TABLE IF EXISTS ONLY public.session_weapon_states DROP CONSTRAINT IF EXISTS uq_session_weapon_instance;
ALTER TABLE IF EXISTS ONLY public.session_weapon_states DROP CONSTRAINT IF EXISTS session_weapon_states_pkey;
ALTER TABLE IF EXISTS ONLY public.session_mechs DROP CONSTRAINT IF EXISTS session_mechs_pkey;
ALTER TABLE IF EXISTS ONLY public.session_mech_weapons DROP CONSTRAINT IF EXISTS session_mech_weapons_pkey;
ALTER TABLE IF EXISTS ONLY public.session_mech_attachments DROP CONSTRAINT IF EXISTS session_mech_attachments_pkey;
ALTER TABLE IF EXISTS ONLY public.session_events DROP CONSTRAINT IF EXISTS session_events_pkey;
ALTER TABLE IF EXISTS ONLY public.mechs DROP CONSTRAINT IF EXISTS mechs_pkey;
ALTER TABLE IF EXISTS ONLY public.mech_weapons DROP CONSTRAINT IF EXISTS mech_weapons_pkey;
ALTER TABLE IF EXISTS ONLY public.mech_attachment_link DROP CONSTRAINT IF EXISTS mech_attachment_link_pkey;
ALTER TABLE IF EXISTS ONLY public.game_sessions DROP CONSTRAINT IF EXISTS game_sessions_pkey;
ALTER TABLE IF EXISTS ONLY public.ammo_types DROP CONSTRAINT IF EXISTS ammo_types_pkey;
ALTER TABLE IF EXISTS ONLY public.alembic_version DROP CONSTRAINT IF EXISTS alembic_version_pkc;
ALTER TABLE IF EXISTS public.weapons_master ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.session_weapon_states ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.session_mechs ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.session_mech_weapons ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.session_mech_attachments ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.session_events ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.mechs ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.mech_weapons ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.game_sessions ALTER COLUMN id DROP DEFAULT;
DROP SEQUENCE IF EXISTS public.weapons_master_id_seq;
DROP TABLE IF EXISTS public.weapons_master;
DROP TABLE IF EXISTS public.weapon_attachment_link;
DROP TABLE IF EXISTS public.weapon_ammo_link;
DROP SEQUENCE IF EXISTS public.session_weapon_states_id_seq;
DROP TABLE IF EXISTS public.session_weapon_states;
DROP SEQUENCE IF EXISTS public.session_mechs_id_seq;
DROP TABLE IF EXISTS public.session_mechs;
DROP SEQUENCE IF EXISTS public.session_mech_weapons_id_seq;
DROP TABLE IF EXISTS public.session_mech_weapons;
DROP SEQUENCE IF EXISTS public.session_mech_attachments_id_seq;
DROP TABLE IF EXISTS public.session_mech_attachments;
DROP SEQUENCE IF EXISTS public.session_events_id_seq;
DROP TABLE IF EXISTS public.session_events;
DROP SEQUENCE IF EXISTS public.mechs_id_seq;
DROP TABLE IF EXISTS public.mechs;
DROP SEQUENCE IF EXISTS public.mech_weapons_id_seq;
DROP TABLE IF EXISTS public.mech_weapons;
DROP TABLE IF EXISTS public.mech_attachment_link;
DROP SEQUENCE IF EXISTS public.game_sessions_id_seq;
DROP TABLE IF EXISTS public.game_sessions;
DROP TABLE IF EXISTS public.attachments;
DROP TABLE IF EXISTS public.ammo_types;
DROP TABLE IF EXISTS public.alembic_version;
DROP TYPE IF EXISTS public."weaponType";
DROP TYPE IF EXISTS public.techbaseenum;
DROP TYPE IF EXISTS public."techBaseEnum";
DROP TYPE IF EXISTS public."attachmentType";
--
-- Name: attachmentType; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public."attachmentType" AS ENUM (
    'WEAPON',
    'MECH'
);


--
-- Name: techBaseEnum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public."techBaseEnum" AS ENUM (
    'IS',
    'CLAN',
    'MIXED'
);


--
-- Name: techbaseenum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.techbaseenum AS ENUM (
    'CLAN',
    'IS',
    'MIXED'
);


--
-- Name: weaponType; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public."weaponType" AS ENUM (
    'MISSILE',
    'BALLISTIC',
    'LASER',
    'PPC',
    'ARTY',
    'OTHER'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: ammo_types; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ammo_types (
    sku character varying(50) NOT NULL,
    display_name character varying(100) NOT NULL,
    damage integer,
    heat integer,
    special_effect character varying(50),
    description text
);


--
-- Name: attachments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.attachments (
    sku character varying(50) NOT NULL,
    display_name character varying(100) NOT NULL,
    to_hit_modifier integer,
    tonnage double precision,
    description text,
    attachment_type public."attachmentType",
    cluster_modifier integer,
    tech_base public."techBaseEnum",
    allowed_on character varying[]
);


--
-- Name: game_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.game_sessions (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    status character varying(20) DEFAULT 'active'::character varying NOT NULL,
    current_turn integer DEFAULT 0 NOT NULL,
    created_on timestamp with time zone
);


--
-- Name: game_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.game_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: game_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.game_sessions_id_seq OWNED BY public.game_sessions.id;


--
-- Name: mech_attachment_link; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.mech_attachment_link (
    mech_id integer NOT NULL,
    attachment_sku character varying(50) NOT NULL
);


--
-- Name: mech_weapons; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.mech_weapons (
    id integer NOT NULL,
    mech_id integer NOT NULL,
    weapon_id integer NOT NULL,
    count integer DEFAULT 1 NOT NULL,
    location character varying(50) NOT NULL
);


--
-- Name: mech_weapons_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.mech_weapons_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: mech_weapons_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.mech_weapons_id_seq OWNED BY public.mech_weapons.id;


--
-- Name: mechs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.mechs (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    tech_base public.techbaseenum NOT NULL,
    model character varying(50),
    tonnage integer NOT NULL
);


--
-- Name: mechs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.mechs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: mechs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.mechs_id_seq OWNED BY public.mechs.id;


--
-- Name: session_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.session_events (
    id integer NOT NULL,
    session_id integer NOT NULL,
    turn integer DEFAULT 0 NOT NULL,
    event_type character varying(30) DEFAULT 'fire'::character varying NOT NULL,
    session_mech_id integer,
    attacker character varying(100),
    target character varying(100),
    payload json NOT NULL
);


--
-- Name: session_events_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.session_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: session_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.session_events_id_seq OWNED BY public.session_events.id;


--
-- Name: session_mech_attachments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.session_mech_attachments (
    id integer NOT NULL,
    session_mech_id integer NOT NULL,
    attachment_sku character varying(50) NOT NULL,
    destroyed boolean DEFAULT false NOT NULL
);


--
-- Name: session_mech_attachments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.session_mech_attachments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: session_mech_attachments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.session_mech_attachments_id_seq OWNED BY public.session_mech_attachments.id;


--
-- Name: session_mech_weapons; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.session_mech_weapons (
    id integer NOT NULL,
    session_mech_id integer NOT NULL,
    weapon_id integer NOT NULL,
    location character varying(50) NOT NULL,
    disabled boolean DEFAULT false NOT NULL,
    destroyed boolean DEFAULT false NOT NULL
);


--
-- Name: session_mech_weapons_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.session_mech_weapons_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: session_mech_weapons_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.session_mech_weapons_id_seq OWNED BY public.session_mech_weapons.id;


--
-- Name: session_mechs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.session_mechs (
    id integer NOT NULL,
    session_id integer NOT NULL,
    mech_id integer NOT NULL,
    team character varying(20) DEFAULT 'player'::character varying NOT NULL,
    pilot_name character varying(100),
    pilot_gunnery_skill integer DEFAULT 4 NOT NULL,
    accent_color character varying(30)
);


--
-- Name: session_mechs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.session_mechs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: session_mechs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.session_mechs_id_seq OWNED BY public.session_mechs.id;


--
-- Name: session_weapon_states; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.session_weapon_states (
    id integer NOT NULL,
    session_mech_id integer NOT NULL,
    weapon_key character varying(50) NOT NULL,
    disabled boolean DEFAULT true NOT NULL
);


--
-- Name: session_weapon_states_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.session_weapon_states_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: session_weapon_states_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.session_weapon_states_id_seq OWNED BY public.session_weapon_states.id;


--
-- Name: weapon_ammo_link; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.weapon_ammo_link (
    weapon_id integer NOT NULL,
    ammo_sku character varying(50) NOT NULL
);


--
-- Name: weapon_attachment_link; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.weapon_attachment_link (
    weapon_id integer NOT NULL,
    attachment_sku character varying(50) NOT NULL
);


--
-- Name: weapons_master; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.weapons_master (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    use_ammo boolean,
    damage integer,
    heat integer,
    minimum_range integer,
    short_range integer,
    medium_range integer,
    long_range integer,
    full_name character varying(100),
    short_range_damage integer,
    medium_range_damage integer,
    long_range_damage integer,
    variable_damage boolean DEFAULT false NOT NULL,
    cluster boolean DEFAULT false NOT NULL,
    short_range_modifier integer,
    medium_range_modifier integer,
    long_range_modifier integer,
    num_shots integer,
    cluster_damage integer,
    modifications json,
    tech_base public."techBaseEnum",
    type public."weaponType"
);


--
-- Name: weapons_master_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.weapons_master_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: weapons_master_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.weapons_master_id_seq OWNED BY public.weapons_master.id;


--
-- Name: game_sessions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game_sessions ALTER COLUMN id SET DEFAULT nextval('public.game_sessions_id_seq'::regclass);


--
-- Name: mech_weapons id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mech_weapons ALTER COLUMN id SET DEFAULT nextval('public.mech_weapons_id_seq'::regclass);


--
-- Name: mechs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mechs ALTER COLUMN id SET DEFAULT nextval('public.mechs_id_seq'::regclass);


--
-- Name: session_events id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_events ALTER COLUMN id SET DEFAULT nextval('public.session_events_id_seq'::regclass);


--
-- Name: session_mech_attachments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_mech_attachments ALTER COLUMN id SET DEFAULT nextval('public.session_mech_attachments_id_seq'::regclass);


--
-- Name: session_mech_weapons id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_mech_weapons ALTER COLUMN id SET DEFAULT nextval('public.session_mech_weapons_id_seq'::regclass);


--
-- Name: session_mechs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_mechs ALTER COLUMN id SET DEFAULT nextval('public.session_mechs_id_seq'::regclass);


--
-- Name: session_weapon_states id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_weapon_states ALTER COLUMN id SET DEFAULT nextval('public.session_weapon_states_id_seq'::regclass);


--
-- Name: weapons_master id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weapons_master ALTER COLUMN id SET DEFAULT nextval('public.weapons_master_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.alembic_version (version_num) FROM stdin;
0ee1ce3d0519
\.


--
-- Data for Name: ammo_types; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.ammo_types (sku, display_name, damage, heat, special_effect, description) FROM stdin;
\.


--
-- Data for Name: attachments; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.attachments (sku, display_name, to_hit_modifier, tonnage, description, attachment_type, cluster_modifier, tech_base, allowed_on) FROM stdin;
\.


--
-- Data for Name: game_sessions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.game_sessions (id, name, status, current_turn, created_on) FROM stdin;
3	Train Robbery	completed	1	2026-08-02 21:38:31.764992+00
4	Defend Mobile Field Bases	completed	1	2026-08-02 21:38:31.764992+00
7	City Infiltration	completed	5	2026-08-02 21:38:31.764992+00
10	Foo	in_progress	1	2026-09-06 01:01:52.038951+00
11	YES	in_progress	1	2026-09-06 01:01:52.038951+00
\.


--
-- Data for Name: mech_attachment_link; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.mech_attachment_link (mech_id, attachment_sku) FROM stdin;
\.


--
-- Data for Name: mech_weapons; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.mech_weapons (id, mech_id, weapon_id, count, location) FROM stdin;
85	14	1	1	Center Torso
86	31	14	1	Center Torso
87	24	2	1	Center Torso
88	33	19	6	CT
\.


--
-- Data for Name: mechs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.mechs (id, name, tech_base, model, tonnage) FROM stdin;
1	Uller	CLAN	G	30
2	Fire Moth	CLAN	Prime	20
3	Viper	CLAN	A	40
4	Locust	CLAN	IIC	25
5	Champion	CLAN	C	60
6	Thunderbolt	CLAN	C	65
7	Adder	CLAN	Prime	35
8	Huntsman	CLAN	B	50
9	Loki	CLAN	A	65
10	LRM BOAT	CLAN	Prime	50
11	Ryoken	CLAN	Prime	50
12	Spector	CLAN	Prime	50
13	Wraith	CLAN		50
14	Falconer	CLAN		50
15	Beserker	CLAN		50
16	Timberwolf	CLAN		50
17	Nightsky	CLAN		50
18	Thanatos	CLAN		50
19	Uziel	CLAN		50
20	King Crab	CLAN		50
21	Sagittaire	CLAN	Prime	50
22	Maelstrom	CLAN	Prime	50
23	Annihilator	CLAN	Prime	50
24	TEST MECH	CLAN	Prime	50
25	Shadow Hawk	CLAN	IIC	45
26	Griffin	CLAN	IIC	40
27	Phoenix Hawk	CLAN	IIC	80
28	Jenner	CLAN	IIC	35
29	Archer	CLAN	C	70
30	Guillotine	CLAN	IIC	70
31	Hunchback	CLAN	IIC	85
32	Battlemaster	CLAN	C	85
33	Atlas	CLAN	C	100
34	Turkina	CLAN	Prime	95
35	Warhammer	CLAN	IIC	80
\.


--
-- Data for Name: session_events; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.session_events (id, session_id, turn, event_type, session_mech_id, attacker, target, payload) FROM stdin;
71	11	1	fire	92	Atlas	Archer	{"attacker": "Atlas", "target": "Archer", "target_movement_modifier": 0, "shots": [{"weapon": "Clan Ultra AC20", "target_number": 4, "target_facing": "Front/Rear", "range_band": "SHORT", "roll": 8, "hit": true, "hit_location": null, "damage": 40, "critical_hit": false, "all_rolls": {"to_hit_1": 6, "to_hit_2": 2, "location_1": null, "location_2": null, "tac_reroll_1": null, "tac_reroll_2": null}, "cluster_roll": 8, "cluster_hits_landed": 2, "cluster_hits": [{"location": "Center Torso", "damage": 20, "critical_hit": false}, {"location": "Left Leg", "damage": 20, "critical_hit": false}]}, {"weapon": "Clan Ultra AC20", "target_number": 4, "target_facing": "Front/Rear", "range_band": "SHORT", "roll": 9, "hit": true, "hit_location": null, "damage": 40, "critical_hit": false, "all_rolls": {"to_hit_1": 6, "to_hit_2": 3, "location_1": null, "location_2": null, "tac_reroll_1": null, "tac_reroll_2": null}, "cluster_roll": 8, "cluster_hits_landed": 2, "cluster_hits": [{"location": "Right Torso", "damage": 20, "critical_hit": false}, {"location": "Left Leg", "damage": 20, "critical_hit": false}]}, {"weapon": "Clan Ultra AC20", "target_number": 4, "target_facing": "Front/Rear", "range_band": "SHORT", "roll": 7, "hit": true, "hit_location": null, "damage": 20, "critical_hit": false, "all_rolls": {"to_hit_1": 6, "to_hit_2": 1, "location_1": null, "location_2": null, "tac_reroll_1": null, "tac_reroll_2": null}, "cluster_roll": 6, "cluster_hits_landed": 1, "cluster_hits": [{"location": "Left Leg", "damage": 20, "critical_hit": false}]}, {"weapon": "Clan Ultra AC20", "target_number": 4, "target_facing": "Front/Rear", "range_band": "SHORT", "roll": 10, "hit": true, "hit_location": null, "damage": 20, "critical_hit": false, "all_rolls": {"to_hit_1": 5, "to_hit_2": 5, "location_1": null, "location_2": null, "tac_reroll_1": null, "tac_reroll_2": null}, "cluster_roll": 4, "cluster_hits_landed": 1, "cluster_hits": [{"location": "Right Leg", "damage": 20, "critical_hit": false}]}, {"weapon": "Clan Ultra AC20", "target_number": 4, "target_facing": "Front/Rear", "range_band": "SHORT", "roll": 12, "hit": true, "hit_location": null, "damage": 20, "critical_hit": false, "all_rolls": {"to_hit_1": 6, "to_hit_2": 6, "location_1": null, "location_2": null, "tac_reroll_1": null, "tac_reroll_2": null}, "cluster_roll": 4, "cluster_hits_landed": 1, "cluster_hits": [{"location": "Center Torso", "damage": 20, "critical_hit": false}]}, {"weapon": "Clan Ultra AC20", "target_number": 4, "target_facing": "Front/Rear", "range_band": "SHORT", "roll": 6, "hit": true, "hit_location": null, "damage": 20, "critical_hit": false, "all_rolls": {"to_hit_1": 2, "to_hit_2": 4, "location_1": null, "location_2": null, "tac_reroll_1": null, "tac_reroll_2": null}, "cluster_roll": 4, "cluster_hits_landed": 1, "cluster_hits": [{"location": "Right Leg", "damage": 20, "critical_hit": false}]}], "hits": 6, "misses": 0, "total_damage": 160, "total_heat": 42, "unresolved_weapons": [], "turn": 1}
\.


--
-- Data for Name: session_mech_attachments; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.session_mech_attachments (id, session_mech_id, attachment_sku, destroyed) FROM stdin;
\.


--
-- Data for Name: session_mech_weapons; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.session_mech_weapons (id, session_mech_id, weapon_id, location, disabled, destroyed) FROM stdin;
93	92	19	CT	f	f
94	92	19	CT	f	f
95	92	19	CT	f	f
96	92	19	CT	f	f
97	92	19	CT	f	f
98	92	19	CT	f	f
\.


--
-- Data for Name: session_mechs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.session_mechs (id, session_id, mech_id, team, pilot_name, pilot_gunnery_skill, accent_color) FROM stdin;
14	3	2	player	Clan Mechwarrior	3	\N
15	3	3	player	Clan Mechwarrior	3	\N
16	3	4	player	Clan Mechwarrior	3	\N
17	4	1	player	Clan Mechwarrior	3	\N
18	4	2	player	Clan Mechwarrior	3	\N
26	3	15	enemy	Carl	4	\N
27	3	16	enemy	Stokved	4	\N
28	3	17	enemy	Wolff	4	\N
29	3	18	enemy	Jung	4	\N
30	3	19	enemy	Lyta	4	\N
32	4	21	enemy	Paul	4	\N
33	4	22	enemy	Christ	4	\N
34	4	23	enemy	Bob	4	\N
35	4	20	enemy	Susan	4	\N
41	7	5	player	Clan Mechwarrior	3	\N
42	7	6	player	Clan Mechwarrior	3	\N
43	7	7	player	Clan Mechwarrior	2	\N
44	7	8	player	Clan Mechwarrior	3	\N
45	7	9	player	Clan Mechwarrior	3	\N
46	7	6	player	Clan Mechwarrior	3	\N
47	7	6	player	Clan Mechwarrior	3	\N
48	7	15	enemy	\N	4	\N
49	7	16	enemy	\N	4	\N
50	7	17	enemy	\N	4	\N
51	7	18	enemy	\N	4	\N
52	7	19	enemy	\N	4	\N
53	7	11	enemy	\N	4	\N
54	7	14	enemy	\N	4	\N
55	7	13	enemy	\N	4	\N
56	7	12	enemy	\N	4	\N
87	10	23	player	Bob	4	amber
88	10	26	player	Ryan	4	rose
89	10	12	player	Joe	4	violet
90	10	32	enemy	\N	4	\N
91	10	31	enemy	\N	4	\N
92	11	33	player	Captain Robert Smalls	4	amber
93	11	29	enemy	\N	4	\N
\.


--
-- Data for Name: session_weapon_states; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.session_weapon_states (id, session_mech_id, weapon_key, disabled) FROM stdin;
1	44	16#0	t
2	44	17#0	t
4	44	18#0	t
5	44	17#1	t
6	44	18#1	t
7	44	19#0	t
8	43	3#0	t
9	43	4#0	t
\.


--
-- Data for Name: weapon_ammo_link; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.weapon_ammo_link (weapon_id, ammo_sku) FROM stdin;
\.


--
-- Data for Name: weapon_attachment_link; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.weapon_attachment_link (weapon_id, attachment_sku) FROM stdin;
\.


--
-- Data for Name: weapons_master; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.weapons_master (id, name, use_ammo, damage, heat, minimum_range, short_range, medium_range, long_range, full_name, short_range_damage, medium_range_damage, long_range_damage, variable_damage, cluster, short_range_modifier, medium_range_modifier, long_range_modifier, num_shots, cluster_damage, modifications, tech_base, type) FROM stdin;
1	CERLL	f	10	12	\N	8	15	25	Clan ER Large Laser	\N	\N	\N	f	f	\N	\N	\N	\N	\N	\N	\N	\N
2	CERML	f	7	5	\N	5	10	15	Clan ER Medium Laser	\N	\N	\N	f	f	\N	\N	\N	\N	\N	\N	\N	\N
3	CLRM10	t	10	4	\N	7	14	21	Clan LRM10	\N	\N	\N	f	f	\N	\N	\N	10	5	\N	\N	\N
4	CSRM6	t	12	4	\N	3	6	9	Clan SRM6	\N	\N	\N	f	f	\N	\N	\N	6	2	\N	\N	\N
5	CSRM4	t	8	3	\N	3	6	9	Clan SRM4	\N	\N	\N	f	f	\N	\N	\N	4	2	\N	\N	\N
6	CMPL	f	7	4	\N	4	8	12	Clan Medium Pulse Laser	\N	\N	\N	f	f	-2	-2	-2	\N	\N	\N	\N	\N
7	CERSL	f	5	2	\N	2	4	6	Clan ER Small Laser	\N	\N	\N	f	f	\N	\N	\N	\N	\N	\N	\N	\N
8	CLBX10	t	10	2	\N	6	12	18	Clan LBX10	\N	\N	\N	f	f	\N	\N	\N	\N	\N	\N	\N	\N
9	CSPL	f	3	2	\N	2	4	6	Clan Small Pulse Laser	\N	\N	\N	f	f	-2	-2	-2	\N	\N	\N	\N	\N
10	CLPL	f	10	10	\N	6	14	20	Clan Large Pulse Laser	\N	\N	\N	f	f	-2	-2	-2	\N	\N	\N	\N	\N
11	CERPPC	f	15	15	\N	7	14	23	Clan ERPPC	\N	\N	\N	f	f	\N	\N	\N	\N	\N	\N	\N	\N
12	CMG	t	2	0	\N	1	2	3	Clan Machine Gun	\N	\N	\N	f	f	\N	\N	\N	\N	\N	\N	\N	\N
14	CLRM20	t	20	6	\N	7	14	21	Clan LRM20	\N	\N	\N	f	f	\N	\N	\N	20	5	\N	\N	\N
13	CUAC5	t	10	1	\N	7	14	21	Clan Ultra AC5	\N	\N	\N	f	f	\N	\N	\N	2	5	{"weapon_type": "ULTRA"}	\N	BALLISTIC
15	CSSRM2	t	4	2	\N	4	8	12	Clan Streak SRM 2	\N	\N	\N	f	f	\N	\N	\N	2	2	{"weapon_type": "STREAK"}	\N	MISSILE
16	CLRM5	t	5	2	\N	7	14	21	Clan LRM 5	\N	\N	\N	f	f	\N	\N	\N	5	5	null	\N	MISSILE
17	CUAC10	t	20	3	\N	6	12	18	Clan Ultra AC10	\N	\N	\N	f	f	\N	\N	\N	2	10	{"weapon_type": "ULTRA"}	\N	BALLISTIC
18	CSSRM4	t	8	0	\N	4	8	12	Clan Streak SRM 4	\N	\N	\N	f	f	\N	\N	\N	4	2	{"weapon_type": "STREAK"}	\N	MISSILE
19	CUAC20	t	40	7	\N	4	8	12	Clan Ultra AC20	\N	\N	\N	f	f	\N	\N	\N	2	20	{"weapon_type": "ULTRA"}	\N	BALLISTIC
20	ML	f	5	3	\N	3	6	9	Medium Laser	\N	\N	\N	f	f	\N	\N	\N	\N	\N	null	\N	LASER
\.


--
-- Name: game_sessions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.game_sessions_id_seq', 11, true);


--
-- Name: mech_weapons_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.mech_weapons_id_seq', 88, true);


--
-- Name: mechs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.mechs_id_seq', 35, true);


--
-- Name: session_events_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.session_events_id_seq', 71, true);


--
-- Name: session_mech_attachments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.session_mech_attachments_id_seq', 1, false);


--
-- Name: session_mech_weapons_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.session_mech_weapons_id_seq', 98, true);


--
-- Name: session_mechs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.session_mechs_id_seq', 93, true);


--
-- Name: session_weapon_states_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.session_weapon_states_id_seq', 9, true);


--
-- Name: weapons_master_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.weapons_master_id_seq', 20, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: ammo_types ammo_types_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ammo_types
    ADD CONSTRAINT ammo_types_pkey PRIMARY KEY (sku);


--
-- Name: game_sessions game_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game_sessions
    ADD CONSTRAINT game_sessions_pkey PRIMARY KEY (id);


--
-- Name: mech_attachment_link mech_attachment_link_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mech_attachment_link
    ADD CONSTRAINT mech_attachment_link_pkey PRIMARY KEY (mech_id, attachment_sku);


--
-- Name: mech_weapons mech_weapons_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mech_weapons
    ADD CONSTRAINT mech_weapons_pkey PRIMARY KEY (id);


--
-- Name: mechs mechs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mechs
    ADD CONSTRAINT mechs_pkey PRIMARY KEY (id);


--
-- Name: session_events session_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_events
    ADD CONSTRAINT session_events_pkey PRIMARY KEY (id);


--
-- Name: session_mech_attachments session_mech_attachments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_mech_attachments
    ADD CONSTRAINT session_mech_attachments_pkey PRIMARY KEY (id);


--
-- Name: session_mech_weapons session_mech_weapons_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_mech_weapons
    ADD CONSTRAINT session_mech_weapons_pkey PRIMARY KEY (id);


--
-- Name: session_mechs session_mechs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_mechs
    ADD CONSTRAINT session_mechs_pkey PRIMARY KEY (id);


--
-- Name: session_weapon_states session_weapon_states_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_weapon_states
    ADD CONSTRAINT session_weapon_states_pkey PRIMARY KEY (id);


--
-- Name: session_weapon_states uq_session_weapon_instance; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_weapon_states
    ADD CONSTRAINT uq_session_weapon_instance UNIQUE (session_mech_id, weapon_key);


--
-- Name: weapon_ammo_link weapon_ammo_link_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weapon_ammo_link
    ADD CONSTRAINT weapon_ammo_link_pkey PRIMARY KEY (weapon_id, ammo_sku);


--
-- Name: weapon_attachment_link weapon_attachment_link_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weapon_attachment_link
    ADD CONSTRAINT weapon_attachment_link_pkey PRIMARY KEY (weapon_id, attachment_sku);


--
-- Name: attachments weapon_attachments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attachments
    ADD CONSTRAINT weapon_attachments_pkey PRIMARY KEY (sku);


--
-- Name: weapons_master weapons_master_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weapons_master
    ADD CONSTRAINT weapons_master_name_key UNIQUE (name);


--
-- Name: weapons_master weapons_master_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weapons_master
    ADD CONSTRAINT weapons_master_pkey PRIMARY KEY (id);


--
-- Name: ix_session_events_session_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_session_events_session_id ON public.session_events USING btree (session_id);


--
-- Name: mech_attachment_link mech_attachment_link_attachment_sku_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mech_attachment_link
    ADD CONSTRAINT mech_attachment_link_attachment_sku_fkey FOREIGN KEY (attachment_sku) REFERENCES public.attachments(sku) ON DELETE CASCADE;


--
-- Name: mech_attachment_link mech_attachment_link_mech_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mech_attachment_link
    ADD CONSTRAINT mech_attachment_link_mech_id_fkey FOREIGN KEY (mech_id) REFERENCES public.mechs(id) ON DELETE CASCADE;


--
-- Name: mech_weapons mech_weapons_mech_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mech_weapons
    ADD CONSTRAINT mech_weapons_mech_id_fkey FOREIGN KEY (mech_id) REFERENCES public.mechs(id) ON DELETE CASCADE;


--
-- Name: mech_weapons mech_weapons_weapon_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mech_weapons
    ADD CONSTRAINT mech_weapons_weapon_id_fkey FOREIGN KEY (weapon_id) REFERENCES public.weapons_master(id) ON DELETE RESTRICT;


--
-- Name: session_events session_events_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_events
    ADD CONSTRAINT session_events_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.game_sessions(id) ON DELETE CASCADE;


--
-- Name: session_events session_events_session_mech_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_events
    ADD CONSTRAINT session_events_session_mech_id_fkey FOREIGN KEY (session_mech_id) REFERENCES public.session_mechs(id) ON DELETE SET NULL;


--
-- Name: session_mech_attachments session_mech_attachments_attachment_sku_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_mech_attachments
    ADD CONSTRAINT session_mech_attachments_attachment_sku_fkey FOREIGN KEY (attachment_sku) REFERENCES public.attachments(sku) ON DELETE RESTRICT;


--
-- Name: session_mech_attachments session_mech_attachments_session_mech_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_mech_attachments
    ADD CONSTRAINT session_mech_attachments_session_mech_id_fkey FOREIGN KEY (session_mech_id) REFERENCES public.session_mechs(id) ON DELETE CASCADE;


--
-- Name: session_mech_weapons session_mech_weapons_session_mech_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_mech_weapons
    ADD CONSTRAINT session_mech_weapons_session_mech_id_fkey FOREIGN KEY (session_mech_id) REFERENCES public.session_mechs(id) ON DELETE CASCADE;


--
-- Name: session_mech_weapons session_mech_weapons_weapon_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_mech_weapons
    ADD CONSTRAINT session_mech_weapons_weapon_id_fkey FOREIGN KEY (weapon_id) REFERENCES public.weapons_master(id) ON DELETE RESTRICT;


--
-- Name: session_mechs session_mechs_mech_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_mechs
    ADD CONSTRAINT session_mechs_mech_id_fkey FOREIGN KEY (mech_id) REFERENCES public.mechs(id) ON DELETE RESTRICT;


--
-- Name: session_mechs session_mechs_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_mechs
    ADD CONSTRAINT session_mechs_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.game_sessions(id) ON DELETE CASCADE;


--
-- Name: session_weapon_states session_weapon_states_session_mech_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_weapon_states
    ADD CONSTRAINT session_weapon_states_session_mech_id_fkey FOREIGN KEY (session_mech_id) REFERENCES public.session_mechs(id) ON DELETE CASCADE;


--
-- Name: weapon_ammo_link weapon_ammo_link_ammo_sku_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weapon_ammo_link
    ADD CONSTRAINT weapon_ammo_link_ammo_sku_fkey FOREIGN KEY (ammo_sku) REFERENCES public.ammo_types(sku) ON DELETE CASCADE;


--
-- Name: weapon_ammo_link weapon_ammo_link_weapon_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weapon_ammo_link
    ADD CONSTRAINT weapon_ammo_link_weapon_id_fkey FOREIGN KEY (weapon_id) REFERENCES public.weapons_master(id) ON DELETE CASCADE;


--
-- Name: weapon_attachment_link weapon_attachment_link_attachment_sku_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weapon_attachment_link
    ADD CONSTRAINT weapon_attachment_link_attachment_sku_fkey FOREIGN KEY (attachment_sku) REFERENCES public.attachments(sku) ON DELETE CASCADE;


--
-- Name: weapon_attachment_link weapon_attachment_link_weapon_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weapon_attachment_link
    ADD CONSTRAINT weapon_attachment_link_weapon_id_fkey FOREIGN KEY (weapon_id) REFERENCES public.weapons_master(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict RkmxuBXOXXzjwiLkacgldlGQpzj9Ztj731RVpTqCHdyR1Fh5dTp9i4yxzSUNfUM

