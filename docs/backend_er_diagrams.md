# Backend ER Diagrams By App

Диаграммы построены по текущим Django models. В каждом разделе:

- основной квадрат содержит все таблицы выбранного приложения;
- квадраты других приложений содержат только таблицы, связанные с выбранным приложением;
- стрелка показывает FK/O2O/M2M направление от таблицы-владельца поля к целевой таблице.

## accounts

```mermaid
flowchart LR
    subgraph accounts_app["accounts"]
        accounts_User["users<br/>User"]
        accounts_CourierProfile["collections_courierprofile<br/>CourierProfile"]
        accounts_EmailVerificationCode["email_verification_codes<br/>EmailVerificationCode"]
    end

    subgraph common_app["common"]
        common_GeoData["geo_data<br/>GeoData"]
    end

    subgraph auth_app["auth"]
        auth_Group["auth_group<br/>Group"]
        auth_Permission["auth_permission<br/>Permission"]
    end

    accounts_User -->|"geodata_id"| common_GeoData
    accounts_CourierProfile -->|"user_id O2O"| accounts_User
    accounts_EmailVerificationCode -->|"user_id"| accounts_User
    accounts_User -.->|"groups M2M"| auth_Group
    accounts_User -.->|"user_permissions M2M"| auth_Permission
```

## common

```mermaid
flowchart LR
    subgraph common_app["common"]
        common_Region["regions<br/>Region"]
        common_City["cities<br/>City"]
        common_GeoData["geo_data<br/>GeoData"]
    end

    subgraph accounts_app["accounts"]
        accounts_User["users<br/>User"]
    end

    subgraph organizations_app["organizations"]
        organizations_OrganizationBranch["organization_branches<br/>OrganizationBranch"]
        organizations_Event["events<br/>Event"]
    end

    subgraph collections_app["collections"]
        collections_Collection["collections_collection<br/>Collection"]
        collections_DonorGroupParameters["collections_donorgroupparameters<br/>DonorGroupParameters"]
        collections_MeetingPlaceProposal["collections_meetingplaceproposal<br/>MeetingPlaceProposal"]
        collections_PollOption["collections_polloption<br/>PollOption"]
    end

    common_City -->|"region_id"| common_Region
    common_GeoData -->|"city_id"| common_City
    accounts_User -->|"geodata_id"| common_GeoData
    organizations_OrganizationBranch -->|"geodata_id"| common_GeoData
    organizations_Event -->|"geodata_id"| common_GeoData
    collections_Collection -->|"geodata_id"| common_GeoData
    collections_DonorGroupParameters -->|"geodata_id"| common_GeoData
    collections_MeetingPlaceProposal -->|"geodata_id"| common_GeoData
    collections_PollOption -->|"geodata_id"| common_GeoData
```

## organizations

```mermaid
flowchart LR
    subgraph organizations_app["organizations"]
        organizations_Category["categories<br/>Category"]
        organizations_Organization["organizations<br/>Organization"]
        organizations_OrganizationMember["organization_members<br/>OrganizationMember"]
        organizations_OrganizationBranch["organization_branches<br/>OrganizationBranch"]
        organizations_OrganizationBranchImage["organization_branch_images<br/>OrganizationBranchImage"]
        organizations_Event["events<br/>Event"]
        organizations_EventImage["event_images<br/>EventImage"]
        organizations_OrganizationNews["organization_news<br/>OrganizationNews"]
        organizations_OrganizationNewsImage["organization_news_images<br/>OrganizationNewsImage"]
        organizations_OrganizationNewsComment["organization_news_comments<br/>OrganizationNewsComment"]
        organizations_OrganizationReportDocument["organization_report_documents<br/>OrganizationReportDocument"]
        organizations_OrganizationRegistrationRequest["organization_registration_requests<br/>OrganizationRegistrationRequest"]
    end

    subgraph accounts_app["accounts"]
        accounts_User["users<br/>User"]
    end

    subgraph common_app["common"]
        common_GeoData["geo_data<br/>GeoData"]
    end

    subgraph collections_app["collections"]
        collections_Collection["collections_collection<br/>Collection"]
        collections_BranchItem["collections_branchitem<br/>BranchItem"]
        collections_DonorGroup["collections_donorgroup<br/>DonorGroup"]
        collections_DonorGroupParameters["collections_donorgroupparameters<br/>DonorGroupParameters"]
        collections_Poll["collections_poll<br/>Poll"]
    end

    subgraph communications_app["communications"]
        communications_OrganizationMessage["organization_messages<br/>OrganizationMessage"]
    end

    organizations_Organization -->|"created_by_id"| accounts_User
    organizations_OrganizationMember -->|"organization_id"| organizations_Organization
    organizations_OrganizationMember -->|"user_id"| accounts_User
    organizations_OrganizationMember -->|"removed_by_id"| accounts_User
    organizations_OrganizationBranch -->|"organization_id"| organizations_Organization
    organizations_OrganizationBranch -->|"geodata_id"| common_GeoData
    organizations_OrganizationBranchImage -->|"branch_id"| organizations_OrganizationBranch
    organizations_Event -->|"category_id"| organizations_Category
    organizations_Event -->|"organization_id"| organizations_Organization
    organizations_Event -->|"geodata_id"| common_GeoData
    organizations_Event -->|"created_by_member_id"| organizations_OrganizationMember
    organizations_EventImage -->|"event_id"| organizations_Event
    organizations_OrganizationNews -->|"organization_id"| organizations_Organization
    organizations_OrganizationNews -->|"created_by_member_id"| organizations_OrganizationMember
    organizations_OrganizationNewsImage -->|"news_id"| organizations_OrganizationNews
    organizations_OrganizationNewsComment -->|"news_id"| organizations_OrganizationNews
    organizations_OrganizationNewsComment -->|"created_by_id"| accounts_User
    organizations_OrganizationReportDocument -->|"organization_id"| organizations_Organization
    organizations_OrganizationReportDocument -->|"created_by_member_id"| organizations_OrganizationMember
    organizations_OrganizationRegistrationRequest -->|"created_by_id"| accounts_User
    organizations_OrganizationRegistrationRequest -->|"reviewed_by_id"| accounts_User
    organizations_OrganizationRegistrationRequest -->|"organization_id O2O"| organizations_Organization

    collections_Collection -->|"organization_id"| organizations_Organization
    collections_Collection -->|"created_by_member_id"| organizations_OrganizationMember
    collections_Collection -->|"branch_id"| organizations_OrganizationBranch
    collections_BranchItem -->|"branch_id"| organizations_OrganizationBranch
    collections_DonorGroup -->|"created_by_member_id"| organizations_OrganizationMember
    collections_DonorGroup -->|"completed_by_member_id"| organizations_OrganizationMember
    collections_DonorGroup -->|"hidden_by_member_id"| organizations_OrganizationMember
    collections_DonorGroupParameters -->|"finalized_by_member_id"| organizations_OrganizationMember
    collections_Poll -->|"news_id"| organizations_OrganizationNews
    collections_Poll -->|"created_by_member_id"| organizations_OrganizationMember
    collections_Poll -->|"finalized_by_member_id"| organizations_OrganizationMember
    communications_OrganizationMessage -->|"organization_id"| organizations_Organization
```

## collections

```mermaid
flowchart LR
    subgraph collections_app["collections"]
        collections_ItemCategory["collections_itemcategory<br/>ItemCategory"]
        collections_Item["collections_item<br/>Item"]
        collections_UserItem["collections_useritem<br/>UserItem"]
        collections_UserItemImage["collections_useritemimage<br/>UserItemImage"]
        collections_Collection["collections_collection<br/>Collection"]
        collections_CollectionItem["collections_collectionitem<br/>CollectionItem"]
        collections_BranchItem["collections_branchitem<br/>BranchItem"]
        collections_DonorGroup["collections_donorgroup<br/>DonorGroup"]
        collections_DonorGroupParameters["collections_donorgroupparameters<br/>DonorGroupParameters"]
        collections_DonorGroupMember["collections_donorgroupmember<br/>DonorGroupMember"]
        collections_DonorGroupItem["collections_donorgroupitem<br/>DonorGroupItem"]
        collections_MeetingPlaceProposal["collections_meetingplaceproposal<br/>MeetingPlaceProposal"]
        collections_Poll["collections_poll<br/>Poll"]
        collections_PollOption["collections_polloption<br/>PollOption"]
        collections_PollVote["collections_pollvote<br/>PollVote"]
        collections_DonorGroupVideoReport["collections_donorgroupvideoreport<br/>DonorGroupVideoReport"]
    end

    subgraph accounts_app["accounts"]
        accounts_User["users<br/>User"]
    end

    subgraph common_app["common"]
        common_GeoData["geo_data<br/>GeoData"]
    end

    subgraph organizations_app["organizations"]
        organizations_Organization["organizations<br/>Organization"]
        organizations_OrganizationMember["organization_members<br/>OrganizationMember"]
        organizations_OrganizationBranch["organization_branches<br/>OrganizationBranch"]
        organizations_OrganizationNews["organization_news<br/>OrganizationNews"]
    end

    subgraph communications_app["communications"]
        communications_DonorGroupMessage["donor_group_messages<br/>DonorGroupMessage"]
    end

    collections_Item -->|"category_id"| collections_ItemCategory
    collections_UserItem -->|"user_id"| accounts_User
    collections_UserItem -->|"category_id"| collections_ItemCategory
    collections_UserItemImage -->|"user_item_id"| collections_UserItem
    collections_Collection -->|"organization_id"| organizations_Organization
    collections_Collection -->|"created_by_member_id"| organizations_OrganizationMember
    collections_Collection -->|"branch_id"| organizations_OrganizationBranch
    collections_Collection -->|"geodata_id"| common_GeoData
    collections_CollectionItem -->|"collection_id"| collections_Collection
    collections_CollectionItem -->|"category_id"| collections_ItemCategory
    collections_BranchItem -->|"branch_id"| organizations_OrganizationBranch
    collections_BranchItem -->|"category_id"| collections_ItemCategory
    collections_DonorGroup -->|"collection_id"| collections_Collection
    collections_DonorGroup -->|"created_by_member_id"| organizations_OrganizationMember
    collections_DonorGroup -->|"completed_by_member_id"| organizations_OrganizationMember
    collections_DonorGroup -->|"hidden_by_member_id"| organizations_OrganizationMember
    collections_DonorGroupParameters -->|"donor_group_id O2O"| collections_DonorGroup
    collections_DonorGroupParameters -->|"geodata_id"| common_GeoData
    collections_DonorGroupParameters -->|"finalized_by_member_id"| organizations_OrganizationMember
    collections_DonorGroupMember -->|"donor_group_id"| collections_DonorGroup
    collections_DonorGroupMember -->|"user_id"| accounts_User
    collections_DonorGroupItem -->|"donor_group_id"| collections_DonorGroup
    collections_DonorGroupItem -->|"user_item_id"| collections_UserItem
    collections_MeetingPlaceProposal -->|"donor_group_id"| collections_DonorGroup
    collections_MeetingPlaceProposal -->|"proposed_by_id"| accounts_User
    collections_MeetingPlaceProposal -->|"geodata_id"| common_GeoData
    collections_Poll -->|"donor_group_id"| collections_DonorGroup
    collections_Poll -->|"news_id"| organizations_OrganizationNews
    collections_Poll -->|"created_by_member_id"| organizations_OrganizationMember
    collections_Poll -->|"source_poll_id"| collections_Poll
    collections_Poll -->|"finalized_option_id"| collections_PollOption
    collections_Poll -->|"finalized_by_member_id"| organizations_OrganizationMember
    collections_PollOption -->|"poll_id"| collections_Poll
    collections_PollOption -->|"geodata_id"| common_GeoData
    collections_PollOption -->|"source_place_proposal_id"| collections_MeetingPlaceProposal
    collections_PollVote -->|"poll_id"| collections_Poll
    collections_PollVote -->|"option_id"| collections_PollOption
    collections_PollVote -->|"user_id"| accounts_User
    collections_DonorGroupVideoReport -->|"donor_group_id"| collections_DonorGroup
    collections_DonorGroupVideoReport -->|"uploaded_by_id"| accounts_User
    communications_DonorGroupMessage -->|"donor_group_id"| collections_DonorGroup
```

## communications

```mermaid
flowchart LR
    subgraph communications_app["communications"]
        communications_Notification["notifications<br/>Notification"]
        communications_UserDevice["user_devices<br/>UserDevice"]
        communications_NotificationDelivery["notification_deliveries<br/>NotificationDelivery"]
        communications_OrganizationMessage["organization_messages<br/>OrganizationMessage"]
        communications_DonorGroupMessage["donor_group_messages<br/>DonorGroupMessage"]
        communications_Invitation["invitations<br/>Invitation"]
    end

    subgraph accounts_app["accounts"]
        accounts_User["users<br/>User"]
    end

    subgraph organizations_app["organizations"]
        organizations_Organization["organizations<br/>Organization"]
    end

    subgraph collections_app["collections"]
        collections_DonorGroup["collections_donorgroup<br/>DonorGroup"]
    end

    subgraph contenttypes_app["contenttypes"]
        contenttypes_ContentType["django_content_type<br/>ContentType"]
    end

    communications_Notification -->|"recipient_id"| accounts_User
    communications_Notification -->|"actor_id"| accounts_User
    communications_UserDevice -->|"user_id"| accounts_User
    communications_NotificationDelivery -->|"notification_id"| communications_Notification
    communications_NotificationDelivery -->|"device_id"| communications_UserDevice
    communications_OrganizationMessage -->|"organization_id"| organizations_Organization
    communications_OrganizationMessage -->|"author_id"| accounts_User
    communications_DonorGroupMessage -->|"donor_group_id"| collections_DonorGroup
    communications_DonorGroupMessage -->|"author_id"| accounts_User
    communications_Invitation -->|"content_type_id"| contenttypes_ContentType
    communications_Invitation -->|"invited_user_id"| accounts_User
    communications_Invitation -->|"invited_by_id"| accounts_User
    communications_Invitation -->|"notification_id O2O"| communications_Notification
    communications_Invitation -.->|"object_id GenericForeignKey"| organizations_Organization
    communications_Invitation -.->|"object_id GenericForeignKey"| collections_DonorGroup
```

