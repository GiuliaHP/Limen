# L'ID unique de ton rig
RIG_ID = "218c3h2c28aa52a6"

# Le dictionnaire des os pour les Snaps IK/FK
IKFK_DATA = {
    "Adult": {
        "Arm L": {
            "prop": "Adult_upper_arm_parent.L",
            "fk": '["Adult_upper_arm_fk.L", "Adult_forearm_fk.L", "Adult_hand_fk.L"]',
            "ik": '["Adult_upper_arm_ik.L", "MCH-Adult_forearm_ik.L", "MCH-Adult_upper_arm_ik_target.L"]',
            "ctrl": '["Adult_upper_arm_ik.L", "Adult_upper_arm_ik_target.L", "Adult_hand_ik.L"]',
            "is_leg": False
        },
        "Arm R": {
            "prop": "Adult_upper_arm_parent.R",
            "fk": '["Adult_upper_arm_fk.R", "Adult_forearm_fk.R", "Adult_hand_fk.R"]',
            "ik": '["Adult_upper_arm_ik.R", "MCH-Adult_forearm_ik.R", "MCH-Adult_upper_arm_ik_target.R"]',
            "ctrl": '["Adult_upper_arm_ik.R", "Adult_upper_arm_ik_target.R", "Adult_hand_ik.R"]',
            "is_leg": False
        },
        "Leg L": {
            "prop": "Adult_thigh_parent.L",
            "fk": '["Adult_thigh_fk.L", "Adult_shin_fk.L", "Adult_foot_fk.L", "Adult_toe_fk.L"]',
            "ik": '["Adult_thigh_ik.L", "MCH-Adult_shin_ik.L", "MCH-Adult_thigh_ik_target.L"]',
            "ctrl": '["Adult_thigh_ik.L", "Adult_thigh_ik_target.L", "Adult_foot_ik.L"]',
            "tail": '["Adult_toe_ik.L"]',
            "extra": '["Adult_foot_heel_ik.L", "Adult_foot_spin_ik.L"]',
            "heel": "Adult_foot_heel_ik.L",
            "is_leg": True
        },
        "Leg R": {
            "prop": "Adult_thigh_parent.R",
            "fk": '["Adult_thigh_fk.R", "Adult_shin_fk.R", "Adult_foot_fk.R", "Adult_toe_fk.R"]',
            "ik": '["Adult_thigh_ik.R", "MCH-Adult_shin_ik.R", "MCH-Adult_thigh_ik_target.R"]',
            "ctrl": '["Adult_thigh_ik.R", "Adult_thigh_ik_target.R", "Adult_foot_ik.R"]',
            "tail": '["Adult_toe_ik.R"]',
            "extra": '["Adult_foot_heel_ik.R", "Adult_foot_spin_ik.R"]',
            "heel": "Adult_foot_heel_ik.R",
            "is_leg": True
        }
    },
    "Child": {
        "Arm L": {
            "prop": "Child_upper_arm_parent.L",
            "fk": '["Child_upper_arm_fk.L", "Child_forearm_fk.L", "Child_hand_fk.L"]',
            "ik": '["Child_upper_arm_ik.L", "MCH-Child_forearm_ik.L", "MCH-Child_upper_arm_ik_target.L"]',
            "ctrl": '["Child_upper_arm_ik.L", "Child_upper_arm_ik_target.L", "Child_hand_ik.L"]',
            "is_leg": False
        },
        "Arm R": {
            "prop": "Child_upper_arm_parent.R",
            "fk": '["Child_upper_arm_fk.R", "Child_forearm_fk.R", "Child_hand_fk.R"]',
            "ik": '["Child_upper_arm_ik.R", "MCH-Child_forearm_ik.R", "MCH-Child_upper_arm_ik_target.R"]',
            "ctrl": '["Child_upper_arm_ik.R", "Child_upper_arm_ik_target.R", "Child_hand_ik.R"]',
            "is_leg": False
        },
        "Leg L": {
            "prop": "Child_thigh_parent.L",
            "fk": '["Child_thigh_fk.L", "Child_shin_fk.L", "Child_foot_fk.L", "Child_toe_fk.L"]',
            "ik": '["Child_thigh_ik.L", "MCH-Child_shin_ik.L", "MCH-Child_thigh_ik_target.L"]',
            "ctrl": '["Child_thigh_ik.L", "Child_thigh_ik_target.L", "Child_foot_ik.L"]',
            "tail": '["Child_toe_ik.L"]',
            "extra": '["Child_foot_heel_ik.L", "Child_foot_spin_ik.L"]',
            "heel": "Child_foot_heel_ik.L",
            "is_leg": True
        },
        "Leg R": {
            "prop": "Child_thigh_parent.R",
            "fk": '["Child_thigh_fk.R", "Child_shin_fk.R", "Child_foot_fk.R", "Child_toe_fk.R"]',
            "ik": '["Child_thigh_ik.R", "MCH-Child_shin_ik.R", "MCH-Child_thigh_ik_target.R"]',
            "ctrl": '["Child_thigh_ik.R", "Child_thigh_ik_target.R", "Child_foot_ik.R"]',
            "tail": '["Child_toe_ik.R"]',
            "extra": '["Child_foot_heel_ik.R", "Child_foot_spin_ik.R"]',
            "heel": "Child_foot_heel_ik.R",
            "is_leg": True
        }
    }
}