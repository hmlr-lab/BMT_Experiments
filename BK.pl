:- style_check(-discontiguous).
:- set_prolog_flag(verbose, silent).
:- dynamic sector/3.
:- dynamic range/3.
:- dynamic dcpa/3.
:- dynamic tcpa/3.
:- dynamic bearing/3.
:- dynamic distance/3.
:- dynamic arc_overtaking/2.     
:- dynamic status/2.
:- dynamic waterway/2.
:- dynamic constraint_draught/1.
:- dynamic clock/1.
:- dynamic applies/3.
:- dynamic applies/2.
:- dynamic role/3.
:- dynamic priority/5.
:- dynamic port_forward/2.
:- dynamic port_aft/2.
:- dynamic starboard_forward/2.
:- dynamic starboard_aft/2.
:- dynamic port/2.
:- dynamic starboard/2.
:- dynamic forward/2.
:- dynamic aft/2.
:- dynamic dcpa_unsafe/2.
:- dynamic dcpa_safe/2.
:- dynamic tcpa_closing/2.
:- dynamic range_actionable/2.
:- dynamic timeliness/3.
:- dynamic risk_collision/2.
:- dynamic close_quarters_developing/2.
:- dynamic close_quarters/2.
:- dynamic port_forward/2.
:- dynamic port_aft/2.
:- dynamic starboard_forward/2.
:- dynamic starboard_aft/2.
:- dynamic port/2.
:- dynamic starboard/2.
:- dynamic forward/2.
:- dynamic aft/2.
:-dynamic role/3.



%  GEOMETRIC ABSTRACTION

%arc_overtaking(X,Y) :- bearing(Y,X,B), B>=10, B=<22.

port_forward(X,Y)      :- sector(X,Y,port_bow_forward).
port_forward(X,Y)      :- sector(X,Y,port_bow_broad).
port_forward(X,Y)      :- sector(X,Y,port_beam_forward).
port_aft(X,Y)          :- sector(X,Y,port_beam_aft).
port_aft(X,Y)          :- sector(X,Y,port_quarter_broad).
port_aft(X,Y)          :- sector(X,Y,port_quarter_aft).
starboard_forward(X,Y) :- sector(X,Y,starboard_bow_forward).
starboard_forward(X,Y) :- sector(X,Y,starboard_bow_broad).
starboard_forward(X,Y) :- sector(X,Y,starboard_beam_forward).
starboard_aft(X,Y)     :- sector(X,Y,starboard_beam_aft).
starboard_aft(X,Y)     :- sector(X,Y,starboard_quarter_broad).
starboard_aft(X,Y)     :- sector(X,Y,starboard_quarter_aft).

port(X,Y)      :- port_forward(X,Y).
port(X,Y)      :- port_aft(X,Y).
port(X,Y)      :- sector(X,Y,port_beam).
starboard(X,Y) :- starboard_forward(X,Y).
starboard(X,Y) :- starboard_aft(X,Y).
starboard(X,Y) :- sector(X,Y,starboard_beam).
forward(X,Y)   :- port_forward(X,Y).
forward(X,Y)   :- starboard_forward(X,Y).
forward(X,Y)   :- sector(X,Y,ahead).
aft(X,Y)       :- port_aft(X,Y).
aft(X,Y)       :- starboard_aft(X,Y).
aft(X,Y)       :- sector(X,Y,astern).


%  CONCEPTUAL GROUPINGS                           

dcpa_unsafe(X,Y) :- dcpa(X,Y,very_close).
dcpa_unsafe(X,Y) :- dcpa(X,Y,close).
dcpa_unsafe(X,Y) :- dcpa(X,Y,near).

dcpa_safe(X,Y) :- dcpa(X,Y,marginal).
dcpa_safe(X,Y) :- dcpa(X,Y,safe).

tcpa_closing(X,Y) :- \+ tcpa(X,Y,opening).

range_actionable(X,Y) :- \+ range(X,Y,very_far).


%  TIMELINESS  (Rule 8(a))                   

timeliness(X,Y,ample)    :- tcpa(X,Y,medium). 
timeliness(X,Y,ample)    :- tcpa(X,Y,long).
timeliness(X,Y,ample)    :- tcpa(X,Y,very_long).
timeliness(X,Y,late)     :- tcpa(X,Y,short).
timeliness(X,Y,extremis) :- tcpa(X,Y,imminent).

%  RISK OF COLLISION (Rule 7)

risk_collision(X,Y) :- dcpa_unsafe(X,Y), tcpa(X,Y,imminent).
risk_collision(X,Y) :- dcpa_unsafe(X,Y), tcpa(X,Y,short).
risk_collision(X,Y) :- dcpa_unsafe(X,Y), tcpa(X,Y,medium).


%  CLOSE-QUARTERS SITUATION (Rule 8)

close_quarters_developing(X,Y) :- dcpa_unsafe(X,Y), tcpa_closing(X,Y), range(X,Y,middle).
close_quarters_developing(X,Y) :- dcpa_unsafe(X,Y), tcpa_closing(X,Y), range(X,Y,far).
close_quarters(X,Y)            :- dcpa_unsafe(X,Y), tcpa_closing(X,Y), range(X,Y,close).
close_quarters(X,Y)            :- dcpa_unsafe(X,Y), tcpa_closing(X,Y), range(X,Y,very_close).


%  VESSEL STATUS / WATERWAY CONTEXT                 

%applies(X,rule18_privilege) :- status(X,nuc).
%applies(X,rule18_privilege) :- status(X,ram).
%applies(X,rule18_privilege) :- status(X,fishing).
%applies(X,rule18_privilege) :- status(X,sail).
%applies(X,rule18_privilege) :- constraint_draught(X).
%applies(X,rule9_narrow) :- waterway(X,narrow_channel).
%applies(X,rule9_narrow) :- waterway(X,in_channel).
%applies(X,rule10_tss)   :- waterway(X,tss).


%  ENCOUNTER CLASSIFICATION (Rules 13 / 14 / 15)

applies(X,Y,rule13_overtaking) :-
    risk_collision(X,Y),
    arc_overtaking(X,Y).

applies(X,Y,rule14_headon) :-
    risk_collision(X,Y),
    sector(X,Y,ahead), sector(Y,X,ahead),
    not(applies(X,Y,rule13_overtaking)),
    not(applies(Y,X,rule13_overtaking)).

applies(X,Y,rule15_crossing) :-
    risk_collision(X,Y),
    not(applies(X,Y,rule13_overtaking)),
    not(applies(Y,X,rule13_overtaking)),
    not(applies(X,Y,rule14_headon)).

%  ROLE  (give-way XOR stand-on, one per vessel) 

role(X,Y,giveway) :- applies(X,Y,rule13_overtaking).             % overtaker gives way
role(X,Y,standon) :- applies(Y,X,rule13_overtaking).             % overtaken stands on
role(X,Y,giveway) :- applies(X,Y,rule15_crossing), starboard(X,Y).
role(X,Y,standon) :- applies(X,Y,rule15_crossing), port(X,Y).
role(X,Y,giveway) :- applies(X,Y,rule14_headon).                 % head-on: both give way



%  DUTIES (Rules 16 / 17)                      

applies(X,Y,rule16_giveway) :- role(X,Y,giveway).

applies(X,Y,rule17a1_standon_maintain) :- role(X,Y,standon), timeliness(X,Y,ample).
applies(X,Y,rule17a2_standon_may_act)  :- role(X,Y,standon), timeliness(X,Y,late).
applies(X,Y,rule17b_standon_must_act)  :- role(X,Y,standon), timeliness(X,Y,extremis).



applies(X,Y,rule2_extremis) :- applies(X,Y,rule14_headon), tcpa(X,Y,imminent), dcpa_unsafe(X,Y).


%  MULTI-VESSEL PRIORITY 

%priority(X,Y,standon,giveway,X) :- role(X,Y,standon), role(Y,X,giveway).
%priority(X,Y,giveway,standon,Y) :- role(X,Y,giveway), role(Y,X,standon).
%priority(X,Y,giveway,giveway,both) :- applies(X,Y,rule14_headon).
